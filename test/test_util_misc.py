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


def test_parse_service_uri():
    uri = 'svc://provider:service'
    provider, service, feature = quest.util.parse_service_uri(uri)
    assert provider == 'provider'
    assert service == 'service'
    assert feature is None

    uri = 'svc://provider:service/feature'
    provider, service, feature = quest.util.parse_service_uri(uri)
    assert provider == 'provider'
    assert service == 'service'
    assert feature == 'feature'

    uri = 'svc://provider:service/feature/with/slashes'
    provider, service, feature = quest.util.parse_service_uri(uri)
    assert provider == 'provider'
    assert service == 'service'
    assert feature == 'feature/with/slashes'


def test_bbox2poly():
    bbox = quest.util.bbox2poly(-244.34479950938268, 6.5895717344199625, -224.63313773902783, 20.882714122571414)

    assert bbox == [[-244.34479950938268, 6.5895717344199625],
                    [-244.34479950938268, 20.882714122571414],
                    [-224.63313773902783, 20.882714122571414],
                    [-224.63313773902783, 6.5895717344199625],
                    [-244.34479950938268, 6.5895717344199625]]
