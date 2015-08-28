"Tests for functions in settings.py"
import dsl
import os


def test_update_settings():
    """Basic test that paths are set correctly and defaults are used
    
    """
    dsl.update_settings(config={'BASE_DIR': 'dsl'})

    assert dsl.settings == {
                'BASE_DIR': 'dsl',
                'CACHE_DIR': os.path.join('dsl', 'cache'),
                'DATA_DIR': os.path.join('dsl', 'data'),
                'CONFIG_FILE': os.path.join('dsl', 'dsl_config.yml'),
                'CONFIG_FILE': os.path.join('dsl', 'dsl_config.yml'),
                'COLLECTIONS_INDEX_FILE': os.path.join('dsl', 'dsl_collections.yml'),
                'WEB_SERVICES': [],
                'LOCAL_SERVICES': [],
            }


def test_update_settings_from_file():
    dsl.update_settings_from_file('files/dsl_config.yml')

    assert dsl.settings == {
            'BASE_DIR': 'dsl',
            'CACHE_DIR': os.path.join('dsl', 'cache'),
            'DATA_DIR': os.path.join('dsl', 'data'),
            'CONFIG_FILE': os.path.join('dsl', 'dsl_config.yml'),
            'CONFIG_FILE': os.path.join('dsl', 'dsl_config.yml'),
            'COLLECTIONS_INDEX_FILE': os.path.join('dsl', 'dsl_collections.yml'),
            'WEB_SERVICES': [],
            'LOCAL_SERVICES': [],
        }