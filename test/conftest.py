import logging
import os
import shutil
import tempfile
import warnings
from time import time

import pytest
import quest

from data import CACHED_SERVICES, DATASET

base_path = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(base_path, 'files')
warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created via a new attribute name", UserWarning)


def pytest_addoption(parser):
    parser.addoption('--update-cache', action='store_true')


def pytest_generate_tests(metafunc):
    if 'api' in metafunc.fixturenames:
        api_params = ['python']

        metafunc.parametrize("api", api_params, indirect=True, scope='session')


def get_or_generate_test_cache(update=False, skip=False):
    test_cache_dir = os.environ.get('QUEST_CACHE_DIR') or os.path.join(quest.util.get_quest_dir(),
                                                                       '.cache', 'test_cache')
    if skip:
        # TODO with features refactor there are some tests that access cache that are not skipped.
        return test_cache_dir
    quest.api.update_settings({'CACHE_DIR': test_cache_dir})
    start = None
    if not os.path.exists(test_cache_dir) or update:
        print('Generating the providers metadata cache for tests. This may take several minutes.')
        start = time()

    # prevent warnings
    warnings.simplefilter('ignore')

    # configure logger for ulmo
    logging.getLogger('ulmo').addHandler(logging.NullHandler())

    provider_plugins = quest.plugins.load_providers()

    for name in CACHED_SERVICES:
        provider, service, _ = quest.util.parse_service_uri(name)
        if provider.startswith('user'):
            continue
        provider_plugin = provider_plugins[provider]

        cache_file = os.path.join(quest.util.get_cache_dir(provider_plugin.name), service + '_catalog.p')
        if update or not os.path.exists(cache_file):
            try:
                print('Updating test cache for service: {0}'.format(name))
                quest.api.get_tags(name, update_cache=update)
            except Exception as e:
                print('The following error prevented the cache for the {0} service from updating: {1}: {2}'
                      .format(name, type(e).__name__, str(e)))

    # re-enable warnings
    warnings.simplefilter('default')

    if start is not None:
        print('Generated test cash in {0} seconds'.format(time() - start))

    return test_cache_dir


@pytest.fixture(scope='session')
def get_base_dir(request, pytestconfig):
    base_dir_obj = tempfile.TemporaryDirectory()
    base_dir = base_dir_obj.name
    update_cache = pytestconfig.getoption('--update-cache')
    skip_cache = pytestconfig.getoption('-m').find('not slow') > -1
    test_cache_dir = get_or_generate_test_cache(update_cache, skip_cache)
    os.mkdir(os.path.join(base_dir, '.cache'))
    os.symlink(test_cache_dir, os.path.join(base_dir, '.cache', 'test_cache'))

    def cleanup():
        base_dir_obj.cleanup()

    request.addfinalizer(cleanup)
    return base_dir


@pytest.fixture(scope='session')
def api(request, get_base_dir):
    if request.param == 'python':
        return quest.api


@pytest.fixture
def reset_settings(api, get_base_dir):
    test_settings = {'BASE_DIR': get_base_dir,
                     'CACHE_DIR': os.path.join('.cache', 'test_cache'),
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


@pytest.fixture
def dataset_save_path(api, reset_projects_dir):
    save_path = os.path.join(reset_projects_dir['BASE_DIR'], 'projects', 'test_data', 'col1', 'usgs-nwis', 'iv',
                             DATASET, '{}.h5'.format(DATASET))
    api.update_metadata(uris=DATASET, quest_metadata={'file_path': save_path})

    return save_path
