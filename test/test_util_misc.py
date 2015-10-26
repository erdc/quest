import dsl
import os
import tempfile

def test_get_dsl_dir():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})
    assert dsl.util.get_dsl_dir() == 'dsl'


def test_get_cache_data_dir():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})

    assert dsl.util.get_cache_dir() == os.path.join('dsl', 'cache')
    assert dsl.util.get_data_dir() == os.path.join('dsl', 'data')

    folder = tempfile.gettempdir()
    dsl.api.update_settings(config={'BASE_DIR': 'dsl', 'CACHE_DIR': folder, 'DATA_DIR': folder})
    assert dsl.util.get_cache_dir() == folder
    assert dsl.util.get_data_dir() == folder


def test_get_collections_index():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})
    assert dsl.util.get_collections_index() == os.path.join('dsl', 'dsl_collections.yml')

    dsl.api.update_settings(config={'BASE_DIR': 'dsl', 'COLLECTIONS_INDEX_FILE': 'my_collections_file.yml'})
    assert dsl.util.get_collections_index() == os.path.join('dsl', 'my_collections_file.yml')

    filename = os.path.join(tempfile.gettempdir(), 'my_collections_file.yml')
    dsl.api.update_settings(config={'BASE_DIR': 'dsl', 'COLLECTIONS_INDEX_FILE': filename})
    assert dsl.util.get_collections_index() == filename
