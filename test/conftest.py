import pytest
import os
import shutil
import tempfile
from threading import Thread
from time import sleep, time
import warnings

import quest
from quest.scripts import rpc_server

base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')


RPC_PORT = 4443
RPC_CLIENT = rpc_server.RPCClient(port=RPC_PORT)


def pytest_addoption(parser):
    parser.addoption('--update-cache', action='store_true')
    parser.addoption('--rpc-only', action='store_true')
    parser.addoption('--python-only', action='store_true')
    parser.addoption('--skip-slow', action='store_true')


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
    print('TIME:', time() - start)

    return test_cache_dir


@pytest.fixture(scope='session')
def get_base_dir(request):
    base_dir = tempfile.mkdtemp()
    update_cache = request.config.getoption('--update-cache')
    skip_cache = request.config.getoption('--skip-slow')
    test_cache_dir = get_or_generate_test_cache(update_cache, skip_cache)
    os.symlink(test_cache_dir, os.path.join(base_dir, 'cache'))

    def cleanup():
        shutil.rmtree(base_dir)

    request.addfinalizer(cleanup)

    return base_dir


server_process = None


def start_rpc_server(base_dir):
    os.chdir(base_dir)
    rpc_server.start_server(port=RPC_PORT, threaded=True)


@pytest.fixture(scope='session')
def api(request, get_base_dir):
    if request.param == 'python':
        return quest.api
    elif request.param == 'rpc':
        global server_process
        server_running = server_process.is_alive() if hasattr(server_process, 'is_alive') else False
        if not server_running:
            server_process = Thread(target=start_rpc_server, args=[get_base_dir])
            server_process.start()
            sleep(1)

        request.addfinalizer(lambda: rpc_server.stop_server(port=RPC_PORT))
    return RPC_CLIENT


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
