"Tests for functions in settings.py"
import quest
import os
import tempfile
import pytest

test_settings = {
    'BASE_DIR': 'quest',
    'CACHE_DIR': 'cache',
    'PROJECTS_DIR': 'projects',
    'USER_SERVICES': [],
}


class TempCWD():

    def __init__(self):
        self.cwd = os.getcwd()

    def __enter__(self):
        os.chdir(tempfile.mkdtemp())

    def __exit__(self, *args):
        os.chdir(self.cwd)


@pytest.fixture
def set_environ(request):
    os.environ['QUEST_DIR'] = tempfile.mkdtemp()

    def clear_environ():
        del os.environ['QUEST_DIR']

    request.addfinalizer(clear_environ)


@pytest.fixture(params=[tempfile.mkdtemp(), 'quest'])
def base_dir(request):
    return request.param


# this test needs to run first because quest is set from environment only
# when BASE_DIR is unset
def test_set_base_path_with_env_var(set_environ):
    settings = quest.api.get_settings()
    del settings['BASE_DIR']
    quest.api.update_settings()

    assert quest.api.get_settings() == {
                'BASE_DIR': os.environ['QUEST_DIR'],
                'CACHE_DIR': 'cache',
                'PROJECTS_DIR': 'projects',
                'USER_SERVICES': [],
                }


def test_update_settings(base_dir):
    """Basic test that paths are set correctly and defaults are used

    """

    with TempCWD():

        quest.api.update_settings(config={'BASE_DIR': base_dir})

        base_dir = base_dir if os.path.isabs(base_dir) else os.path.join(os.getcwd(), base_dir)

        test_settings.update({'BASE_DIR': base_dir})

    assert quest.api.get_settings() == test_settings


def test_update_settings_from_file():
    with TempCWD():
        quest.api.update_settings_from_file(os.path.dirname(os.path.realpath(__file__)) + '/files/quest_config.yml')
        test = test_settings.copy()
        test.update({'USER_SERVICES': ['iraq-vitd', 'usgs-ned1']})
    assert sorted(quest.api.get_settings()['USER_SERVICES']) == (test["USER_SERVICES"])
    assert len(quest.api.get_settings()) == len(test)


def test_save_settings():
    with TempCWD():
        quest.api.update_settings(config={'BASE_DIR': 'quest', 'USER_SERVICES':[]})
        settings = quest.api.get_settings()
        filename = os.path.join(tempfile.gettempdir(), 'quest_config.yml')
        quest.api.save_settings(filename)
        quest.api.update_settings_from_file(filename)

    assert settings == quest.api.get_settings()
