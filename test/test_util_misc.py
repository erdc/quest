import dsl
import os
import tempfile

from conftest import BASE_DIR


def test_get_dsl_dir(reset_projects_dir):
    assert dsl.util.get_dsl_dir() == BASE_DIR


def test_get_cache_data_dir(reset_projects_dir):
    assert dsl.util.get_cache_dir() == os.path.join(BASE_DIR, 'cache')
    assert dsl.util.get_projects_dir() == os.path.join(BASE_DIR, 'projects')

    folder = tempfile.gettempdir()
    dsl.api.update_settings(config={'CACHE_DIR': folder, 'PROJECTS_DIR': folder})
    assert dsl.util.get_cache_dir() == folder
    assert dsl.util.get_projects_dir() == folder
