import pytest
import os
import shutil
import tempfile
from multiprocessing import Process

import quest
from quest.scripts import rpc_server

base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')


TEST_DATA_DIRS = {2: 'python2_data',
                  3: 'python3_data'}

RPC_PORT = 4443
RPC_CLIENT = rpc_server.RPCClient(port=RPC_PORT)


@pytest.fixture(scope='session')
def get_base_dir(request):
    base_dir = tempfile.mkdtemp()

    def cleanup():
        shutil.rmtree(base_dir)

    request.addfinalizer(cleanup)

    return base_dir


server_process = None


def start_rpc_server(base_dir):
    os.chdir(base_dir)
    rpc_server.start_server(port=RPC_PORT, threaded=True)


@pytest.fixture(params=[quest.api, RPC_CLIENT], scope='session', ids=['python', 'rpc'])
def api(request, get_base_dir):
    if request.param == quest.api:
        return request.param
    else:
        global server_process
        server_running = server_process.is_alive() if hasattr(server_process, 'is_alive') else False
        if not server_running:
            server_process = Process(target=start_rpc_server, args=[get_base_dir])
            server_process.start()

        request.addfinalizer(lambda: rpc_server.stop_server(port=RPC_PORT))
    return request.param


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
