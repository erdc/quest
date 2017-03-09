import os
import tempfile
import quest
import pytest


def test_get_quest_dir(reset_projects_dir):
    assert quest.util.get_quest_dir() == reset_projects_dir['BASE_DIR']


@pytest.mark.parametrize('api', [quest.api])
def test_get_cache_data_dir(api, reset_projects_dir):
    assert quest.util.get_cache_dir() == os.path.join(reset_projects_dir['BASE_DIR'], 'cache')
    assert quest.util.get_projects_dir() == os.path.join(reset_projects_dir['BASE_DIR'], 'projects')

    folder = tempfile.gettempdir()
    api.update_settings(config={'CACHE_DIR': folder, 'PROJECTS_DIR': folder})
    assert quest.util.get_cache_dir() == folder
    assert quest.util.get_projects_dir() == folder
