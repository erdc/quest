"Tests for functions in settings.py"
import dsl
import os
import tempfile

test_settings = {
                'BASE_DIR': 'dsl',
                'CACHE_DIR': 'cache',
                'DATA_DIR': 'data',
                'CONFIG_FILE': 'dsl_config.yml',
                'COLLECTIONS_INDEX_FILE': 'dsl_collections.yml',
                'WEB_SERVICES': [],
                'LOCAL_SERVICES': [],
            }


# this test needs to run first because dsl is set from environment only 
# when BASE_DIR is unset
def test_set_base_path_with_env_var():
    os.environ['ENVSIM_DSL_DIR'] = 'dslenv'
    dsl.api.update_settings()

    assert dsl.api.get_settings() == {
                'BASE_DIR': 'dslenv',
                'CACHE_DIR': 'cache',
                'DATA_DIR': 'data',
                'CONFIG_FILE': 'dsl_config.yml',
                'COLLECTIONS_INDEX_FILE': 'dsl_collections.yml',
                'WEB_SERVICES': [],
                'LOCAL_SERVICES': [],
            }


def test_update_settings():
    """Basic test that paths are set correctly and defaults are used
    
    """
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})

    assert dsl.api.get_settings() == test_settings


def test_update_settings_from_file():
    dsl.api.update_settings_from_file('files/dsl_config.yml')

    assert dsl.api.get_settings() == test_settings


def test_save_settings():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})
    filename = os.path.join(tempfile.gettempdir(), 'dsl_config.yml')
    dsl.api.save_settings(filename)
    dsl.api.update_settings_from_file(filename)

    assert dsl.api.get_settings() == test_settings
