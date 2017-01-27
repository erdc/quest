import quest
import os
import tempfile


def test_get_quest_dir(reset_projects_dir):
    assert quest.util.get_quest_dir() == reset_projects_dir['BASE_DIR']


def test_get_cache_data_dir(reset_projects_dir):
    assert quest.util.get_cache_dir() == os.path.join(reset_projects_dir['BASE_DIR'], 'cache')
    assert quest.util.get_projects_dir() == os.path.join(reset_projects_dir['BASE_DIR'], 'projects')

    folder = tempfile.gettempdir()
    quest.api.update_settings(config={'CACHE_DIR': folder, 'PROJECTS_DIR': folder})
    assert quest.util.get_cache_dir() == folder
    assert quest.util.get_projects_dir() == folder
