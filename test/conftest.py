import pytest
import os
import sys
import shutil
import socket
import tempfile
from threading import Thread
from time import sleep, time
import warnings

import quest
from quest.scripts import rpc_server

base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')

# use different default ports for Python 2 and Python 3 so they can both be tested simultaneously
RPC_PORT = 4440 + sys.version_info.major


def pytest_addoption(parser):
    parser.addoption('--update-cache', action='store_true')
    parser.addoption('--rpc-only', action='store_true')
    parser.addoption('--python-only', action='store_true')
    parser.addoption('--skip-slow', action='store_true')
    parser.addoption('--rpc-port-range', dest='rpc_port_range', nargs=2, default=None,
                     help="start and end port for range or ports to scan for an available port.")


def pytest_generate_tests(metafunc):
    if 'api' in metafunc.fixturenames:
        api_params = ['python', 'rpc']
        if metafunc.config.getoption('--python-only'):
            api_params.remove('rpc')
        elif metafunc.config.getoption('--rpc-only'):
            api_params.remove('python')
        metafunc.parametrize("api", api_params, indirect=True, scope='session')


def get_or_generate_test_cache(update=False, skip=False):
    test_cache_dir = os.path.join(quest.util.get_quest_dir(), 'test_cache')
    if skip:
        return test_cache_dir
    start = time()
    quest.api.update_settings({'CACHE_DIR': test_cache_dir})
    if not os.path.exists(test_cache_dir) or update:
        print('Generating the services metadata cache for tests. This may take several minutes.')
    warnings.simplefilter('ignore')
    for name in quest.api.get_services():
        provider, service, feature = quest.util.parse_service_uri(name)
        if provider.startswith('user'):
            continue
        if not update:
            cache_file = os.path.join(quest.util.get_cache_dir(), service + '_features.geojson')
            if os.path.exists(cache_file):
                continue
            driver = quest.util.load_services()[provider]
            cache_file = os.path.join(quest.util.get_cache_dir(driver.name), service + '_features.geojson')
        if update or not os.path.exists(cache_file):
            quest.api.get_features(name, update_cache=update)
    warnings.simplefilter('default')
    print('Generated test cash in {0} seconds'.format(time() - start))

    return test_cache_dir


@pytest.fixture(scope='session')
def get_base_dir(request, pytestconfig):
    base_dir = tempfile.mkdtemp()
    update_cache = request.config.getoption('--update-cache')
    skip_cache = request.config.getoption('--skip-slow')
    test_cache_dir = get_or_generate_test_cache(update_cache, skip_cache)

    if hasattr(os, 'symlink'):
        os.symlink(test_cache_dir, os.path.join(base_dir, 'cache'))
    else:  # for Python 2 on Windows
        shutil.copytree(test_cache_dir, os.path.join(base_dir, 'cache'))

    def cleanup():
        try:
            shutil.rmtree(base_dir)
        except Exception as e:
            capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')
            capmanager.suspendcapture()
            warnings.warn('\nFailed to remove temporary directory {0} due to the following error:\n{1}'
                          .format(base_dir, str(e)))
            capmanager.resumecapture()

    request.addfinalizer(cleanup)

    return base_dir


def get_available_port(request):
    port_range = request.config.getoption('rpc_port_range')
    if port_range is not None:
        port_range = range(int(port_range[0]), int(port_range[1]) + 1)
    else:
        port_range = range(RPC_PORT, RPC_PORT + 1)

    for port in port_range:
        try:
            s = socket.socket()
            s.connect(('localhost', port))
            s.close()
        except socket.error as e:
            if e.errno == 61:  # Connection refused (i.e. port is not being used)
                return port


def start_rpc_server(base_dir, port):
    os.chdir(base_dir)
    rpc_server.start_server(port=port, threaded=True)

server_process = None
port = None


@pytest.fixture(scope='session')
def api(request, get_base_dir):
    if request.param == 'python':
        return quest.api
    elif request.param == 'rpc':
        global server_process
        global port
        server_running = server_process.is_alive() if hasattr(server_process, 'is_alive') else False
        if not server_running:
            port = get_available_port(request)
            server_process = Thread(target=start_rpc_server, args=[get_base_dir, port])
            server_process.start()
            sleep(1)

        request.addfinalizer(lambda: rpc_server.stop_server(port=port))
        return rpc_server.RPCClient(port=port)


@pytest.fixture
def reset_settings(api, get_base_dir):
    test_settings = {'BASE_DIR': get_base_dir,
                     'CACHE_DIR': 'cache',
                     'PROJECTS_DIR': 'projects',
                     'USER_SERVICES': []
                     }

    api.update_settings(test_settings)
    return test_settings


@pytest.fixture
def reset_projects_dir(reset_settings, request):
    base_dir = reset_settings['BASE_DIR']
    projects_dir = os.path.join(base_dir, 'projects')

    def cleanup():
        shutil.rmtree(projects_dir, ignore_errors=True)

    cleanup()
    projects_template_dir = os.path.join(FILES_DIR, 'projects_template')
    shutil.copytree(projects_template_dir, projects_dir)
    request.addfinalizer(cleanup)

    metadata = {'NUMBER_OF_PROJECTS': 4,
                'BASE_DIR': reset_settings['BASE_DIR'],
                }

    return metadata


@pytest.fixture
def set_active_project(api, reset_settings, request):
    previous_active_project = quest.api.get_active_project()
    tests_active_project = getattr(request.module, 'ACTIVE_PROJECT', 'default')
    api.set_active_project(tests_active_project)

    def teardown():
        api.set_active_project(previous_active_project)

    request.addfinalizer(teardown)
