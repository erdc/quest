"Tests for functions in settings.py"
import dsl
import os
import tempfile
import pytest

test_settings = {
    'BASE_DIR': 'dsl',
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
    os.environ['ENVSIM_DSL_DIR'] = tempfile.mkdtemp()

    def clear_environ():
        del os.environ['ENVSIM_DSL_DIR']

    request.addfinalizer(clear_environ)

@pytest.fixture(params=[tempfile.mkdtemp(), 'dsl'])
def base_dir(request):
    return request.param


# this test needs to run first because dsl is set from environment only
# when BASE_DIR is unset
def test_set_base_path_with_env_var(set_environ):
    settings = dsl.api.get_settings()
    del settings['BASE_DIR']
    dsl.api.update_settings()

    assert dsl.api.get_settings() == {
                'BASE_DIR': os.environ['ENVSIM_DSL_DIR'],
                'CACHE_DIR': 'cache',
                'PROJECTS_DIR': 'projects',
                'USER_SERVICES': [],
                }


def test_update_settings(base_dir):
    """Basic test that paths are set correctly and defaults are used

    """

    with TempCWD():

        dsl.api.update_settings(config={'BASE_DIR': base_dir})

        base_dir = base_dir if os.path.isabs(base_dir) else os.path.join(os.getcwd(), base_dir)

        test_settings.update({'BASE_DIR': base_dir})

    assert dsl.api.get_settings() == test_settings


def test_update_settings_from_file():
    with TempCWD():
        dsl.api.update_settings_from_file(os.path.dirname(os.path.realpath(__file__)) + '/files/dsl_config.yml')
        test = test_settings.copy()
        test.update({'USER_SERVICES': ['iraq-vitd', 'usgs-ned1']})
    assert sorted(dsl.api.get_settings()['USER_SERVICES']) == (test["USER_SERVICES"])
    assert len(dsl.api.get_settings()) == len(test)


def test_save_settings():
    with TempCWD():
        dsl.api.update_settings(config={'BASE_DIR': 'dsl', 'USER_SERVICES':[]})
        settings = dsl.api.get_settings()
        filename = os.path.join(tempfile.gettempdir(), 'dsl_config.yml')
        dsl.api.save_settings(filename)
        dsl.api.update_settings_from_file(filename)

    assert settings == dsl.api.get_settings()
