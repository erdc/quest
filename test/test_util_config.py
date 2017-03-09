"Tests for functions in settings.py"
import os
import tempfile
import pytest
import quest
import shutil

test_settings = {
    'BASE_DIR': 'quest',
    'CACHE_DIR': 'cache',
    'PROJECTS_DIR': 'projects',
    'USER_SERVICES': [],
}


class TempCWD():

    def __init__(self):
        self.cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()

    def __enter__(self):
        os.chdir(self.temp_dir)

    def __exit__(self, *args):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp_dir)


@pytest.fixture
def set_environ(request):
    os.environ['QUEST_DIR'] = tempfile.mkdtemp()

    def clear_environ():
        del os.environ['QUEST_DIR']

    request.addfinalizer(clear_environ)


@pytest.fixture(params=[tempfile.mkdtemp(), 'quest'])
def base_dir(request):
    return request.param


def test_set_base_path_with_env_var(set_environ):
    # Can't be tested with the RPC because environmental variable can't be set.
    settings = quest.api.get_settings()
    del settings['BASE_DIR']
    api.update_settings()

    assert api.get_settings() == {
                'BASE_DIR': os.environ['QUEST_DIR'],
                'CACHE_DIR': 'cache',
                'PROJECTS_DIR': 'projects',
                'USER_SERVICES': [],
                }


@pytest.mark.parametrize('api', [quest.api])
def test_update_settings(api, base_dir):
    """Basic test that paths are set correctly and defaults are used

        Can't be tested with RPC because CWD is not the same.
    """

    with TempCWD():

        api.update_settings(config={'BASE_DIR': base_dir})

        base_dir = base_dir if os.path.isabs(base_dir) else os.path.join(os.getcwd(), base_dir)

        test_settings.update({'BASE_DIR': base_dir})

    assert api.get_settings() == test_settings


def test_update_settings_from_file(api):
    with TempCWD():
        api.update_settings_from_file(os.path.dirname(os.path.realpath(__file__)) + '/files/quest_config.yml')
        test = test_settings.copy()
        test.update({'USER_SERVICES': ['iraq-vitd', 'usgs-ned1']})
    assert sorted(api.get_settings()['USER_SERVICES']) == (test["USER_SERVICES"])
    assert len(api.get_settings()) == len(test)


def test_save_settings(api):
    with TempCWD():
        api.update_settings(config={'BASE_DIR': 'quest', 'USER_SERVICES': []})
        settings = api.get_settings()
        filename = os.path.join(tempfile.gettempdir(), 'quest_config.yml')
        api.save_settings(filename)
        api.update_settings_from_file(filename)

    assert settings == api.get_settings()
