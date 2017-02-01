import pytest
import os
import shutil
import sys
import tempfile

import quest

base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')


TEST_DATA_DIRS = {2: 'python2_data',
                  3: 'python3_data'}


@pytest.fixture(scope='session')
def get_base_dir(request):
    base_dir = tempfile.mkdtemp()

    def cleanup():
        shutil.rmtree(base_dir)

    request.addfinalizer(cleanup)

    return base_dir


@pytest.fixture
def reset_settings(get_base_dir):
    test_settings = {'BASE_DIR': get_base_dir,
                     'CACHE_DIR': 'cache',
                     'PROJECTS_DIR': 'projects',
                     'USER_SERVICES': []
                     }

    quest.api.update_settings(test_settings)
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
    python_version = sys.version_info[0]
    test_data_dir = os.path.join(FILES_DIR, TEST_DATA_DIRS[python_version], 'usgs-nwis')
    test_data_dest = os.path.join(projects_dir, 'test_data', 'test_data', 'usgs-nwis')
    shutil.copytree(test_data_dir, test_data_dest)
    request.addfinalizer(cleanup)

    metadata = {'NUMBER_OF_PROJECTS': 4,
                'BASE_DIR': reset_settings['BASE_DIR'],
                }

    return metadata


@pytest.fixture
def set_active_project(reset_settings, request):
    previous_active_project = quest.api.get_active_project()
    tests_active_project = getattr(request.module, 'ACTIVE_PROJECT', 'default')
    quest.api.set_active_project(tests_active_project)

    def teardown():
        quest.api.set_active_project(previous_active_project)

    request.addfinalizer(teardown)
