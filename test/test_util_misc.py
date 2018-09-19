import os
import tempfile
import quest


def test_get_quest_dir(reset_projects_dir):
    assert quest.util.get_quest_dir() == reset_projects_dir['BASE_DIR']


def test_get_cache_data_dir(reset_projects_dir):
    assert quest.util.get_cache_dir() == os.path.join(reset_projects_dir['BASE_DIR'], os.path.join('.cache', 'test_cache'))

    folder_obj = tempfile.TemporaryDirectory()
    folder = folder_obj.name
    quest.api.update_settings(config={'CACHE_DIR': folder})
    assert quest.util.get_cache_dir() == folder


def test_get_project_dir(reset_projects_dir):
    assert quest.util.get_projects_dir() == os.path.join(reset_projects_dir['BASE_DIR'], 'projects')

    folder_obj = tempfile.TemporaryDirectory()
    folder = folder_obj.name
    quest.api.update_settings(config={'PROJECTS_DIR': folder})
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

    bbox = -244.34479950938268, 6.5895717344199625, -224.63313773902783, 20.882714122571414

    poly = quest.util.bbox2poly(*bbox)

    assert poly == [[-244.34479950938268, 6.5895717344199625],
                    [-244.34479950938268, 20.882714122571414],
                    [-224.63313773902783, 20.882714122571414],
                    [-224.63313773902783, 6.5895717344199625],
                    [-244.34479950938268, 6.5895717344199625]]

    bbox = -200, -20, -160, 20

    poly = quest.util.bbox2poly(*bbox, as_geojson=True)

    assert poly == {"coordinates": [],
                    "polygons": [{"coordinates": [[-180, -20.0],
                                                  [-180, 20.0],
                                                  [-160.0, 20.0],
                                                  [-160.0, -20.0],
                                                  [-180, -20.0]],
                                  "type": "Polygon"},
                                 {"coordinates": [[160.0, -20.0],
                                                  [160.0, 20.0],
                                                  [180, 20.0],
                                                  [180, -20.0],
                                                  [160.0, -20.0]],
                                  "type": "Polygon"}],
                    "type": "MultiPolygon"}

    poly = quest.util.bbox2poly(*bbox, as_shapely=True)
    poly = str(poly)

    assert poly == 'MULTIPOLYGON (((-180 -20, -180 20, -160 20, -160 -20, -180 -20)), ' \
                                 '((160 -20, 160 20, 180 20, 180 -20, 160 -20)))'

    bbox = -10, -10, 10, 10

    poly = quest.util.bbox2poly(*bbox, as_geojson=True)

    assert poly == {'coordinates': [[-10.0, -10.0],
                                    [-10.0, 10.0],
                                    [10.0, 10.0],
                                    [10.0, -10.0],
                                    [-10.0, -10.0]],
                    'type': 'Polygon'}

    bbox = 160, -20, 200, 20

    poly = quest.util.bbox2poly(*bbox, as_geojson=True)

    assert poly == {'coordinates': [],
                    'polygons': [{'coordinates': [[160.0, -20.0],
                                                  [160.0, 20.0],
                                                  [180, 20.0],
                                                  [180, -20.0],
                                                  [160.0, -20.0]],
                                  'type': 'Polygon'},
                                 {'coordinates': [[-180, -20.0],
                                                  [-180, 20.0],
                                                  [-160.0, 20.0],
                                                  [-160.0, -20.0],
                                                  [-180, -20.0]],
                                  'type': 'Polygon'}],
                    'type': 'MultiPolygon'}

    poly = quest.util.bbox2poly(*bbox)

    assert poly == [[160.0, -20.0],
                    [160.0, 20.0],
                    [200.0, 20.0],
                    [200.0, -20.0],
                    [160.0, -20.0]]
