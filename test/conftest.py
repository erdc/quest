import pytest
import os
import sys
import shutil
import socket
import tempfile
from threading import Thread
from time import sleep, time
import warnings
import errno
import logging
import quest

from data import CACHED_SERVICES


base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')


def pytest_addoption(parser):
    parser.addoption('--update-cache', action='store_true')
    parser.addoption('--skip-slow', action='store_true')
    parser.addoption('--test-download', action='store_true')


def pytest_generate_tests(metafunc):
    if 'api' in metafunc.fixturenames:
        api_params = ['python']

        metafunc.parametrize("api", api_params, indirect=True, scope='session')


def get_or_generate_test_cache(update=False, skip=False):
    test_cache_dir = os.path.join(quest.util.get_quest_dir(), 'test_cache')
    if skip:
        return test_cache_dir
    quest.api.update_settings({'CACHE_DIR': test_cache_dir})
    start = None
    if not os.path.exists(test_cache_dir) or update:
        print('Generating the services metadata cache for tests. This may take several minutes.')
        start = time()
    warnings.simplefilter('ignore')
    logging.basicConfig()
    drivers = quest.util.load_providers()
    for name in CACHED_SERVICES:
        provider, service, feature = quest.util.parse_service_uri(name)
        if provider.startswith('user'):
            continue
        driver = drivers[provider]
        cache_file = os.path.join(quest.util.get_cache_dir(driver.name), service + '_features.p')
        if update or not os.path.exists(cache_file):
            try:
                print('Updating test cache for service: {0}'.format(name))
                quest.api.get_tags(name, update_cache=update)
            except Exception as e:
                print('The following error prevented the cache for the {0} service from updating: {1}: {2}'
                      .format(name, type(e).__name__, str(e)))
    warnings.simplefilter('default')
    if start is not None:
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


@pytest.fixture(scope='session')
def api(request, get_base_dir):
    if request.param == 'python':
        return quest.api


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
    tests_active_project = getattr(request.module, 'ACTIVE_PROJECT', 'default')
    api.set_active_project(tests_active_project)
