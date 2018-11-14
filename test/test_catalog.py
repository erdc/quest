import pytest

from quest.static import GeomType
from data import SERVICES_CATALOG_COUNT, CACHED_SERVICES

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')

SERVICE_URIS = [
    'svc://usgs-ned:19-arc-second/581d2561e4b08da350d5a3b2',
    'svc://noaa-ncdc:gsod/028140-99999',
    'svc://usgs-nwis:iv/01529950',
]


@pytest.fixture(params=SERVICE_URIS)
def catalog_entry(request):
    return request.param


@pytest.mark.slow
def test_add_datasets(api, catalog_entry):
    b = api.add_datasets('col1', catalog_entry)
    c = api.get_datasets(filters={'collection': 'col1'})
    assert len(list(c)) == 1
    assert b == c


def test_search_catalog_with_no_uris(api):
    catalog_entries = api.search_catalog()
    assert catalog_entries == []


def test_search_catalog_with_collection(api):
    api.set_active_project('test_data')
    catalog_entries = api.search_catalog('col1')
    assert catalog_entries == ['svc://usgs-nwis:iv/01516350']

@pytest.mark.slow
@pytest.mark.parametrize("service, expected, tolerance", SERVICES_CATALOG_COUNT)
def test_search_catalog_from_service(api, service, expected, tolerance):
    catalog_entries = api.search_catalog(service)
    # assert number of catalog entries is within tolerance of expected
    assert abs(len(catalog_entries) - expected) < tolerance


@pytest.mark.slow
def test_search_catalog_with_search_term(api):
    catalog_entries = api.search_catalog('svc://noaa-ncdc:ghcn-daily', filters={'search_terms': ['ZI']})
    expected = 270
    tolerance = 10
    assert abs(len(catalog_entries) - expected) < tolerance


@pytest.mark.slow
def test_search_catalog_with_tag(api):
    catalog_entries = api.search_catalog('svc://noaa-ncdc:ghcn-daily', filters={'country': 'ZI'})
    expected = 20
    tolerance = 5
    assert abs(len(catalog_entries) - expected) < tolerance


@pytest.mark.slow
def test_search_catalog_with_query(api):
    catalog_entries = api.search_catalog('svc://noaa-ncdc:ghcn-daily',
                                queries=["display_name == 'DALGARANGA' or display_name == 'TARDIE STATION'"])
    expected = 2
    tolerance = 1
    assert abs(len(catalog_entries) - expected) < tolerance


def test_new_catalog_entry(api):
    c = api.new_catalog_entry(geom_type=GeomType.POINT, geom_coords=[-94.2, 23.4])
    assert c in api.get_metadata(c)


def test_delete_catalog_entry(api):
    c = api.new_catalog_entry(geom_type=GeomType.POINT, geom_coords=[-94.2, 23.4])
    d = api.new_dataset(collection='col1', catalog_entry=c, source='derived')
    api.delete(d)
    assert d not in api.get_datasets()
    with pytest.raises(KeyError):
        api.get_metadata(c)


def test_delete_derived_dataset(api):
    c = api.new_catalog_entry(geom_type=GeomType.POINT, geom_coords=[-94.2, 23.4])
    d = api.add_datasets(collection='col1', catalog_entries=[c, c])
    api.delete(d[0])
    assert d[0] not in api.get_datasets()
    assert c in api.get_metadata(c)


@pytest.mark.slow
@pytest.mark.parametrize('service', CACHED_SERVICES)
def test_get_tags(api, service):
    tags = api.get_tags(service)
    assert isinstance(tags, dict)
    for value in tags.values():
        assert isinstance(value, list)

