import dsl
import os
import tempfile

def test_get_dsl_dir():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})
    assert dsl.util.get_dsl_dir() == 'dsl'


def test_get_cache_data_dir():
    dsl.api.update_settings(config={'BASE_DIR': 'dsl'})

    assert dsl.util.get_cache_dir() == os.path.join('dsl', 'cache')
    assert dsl.util.get_projects_dir() == os.path.join('dsl', 'projects')

    folder = tempfile.gettempdir()
    dsl.api.update_settings(config={'BASE_DIR': 'dsl', 'CACHE_DIR': folder, 'PROJECTS_DIR': folder})
    assert dsl.util.get_cache_dir() == folder
    assert dsl.util.get_projects_dir() == folder
