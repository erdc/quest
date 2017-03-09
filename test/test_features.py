import pytest

slow = pytest.mark.skipif(
    pytest.config.getoption("--skip-slow"),
    reason="--skip-slow option was set"
)

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')

FEATURE_URIS = []
                # 'svc://usgs-ned:19-arc-second/581d2561e4b08da350d5a3b2',
                # 'svc://ncdc:gsod/028140-99999',
                # 'svc://usgs-nwis:iv/01529950',
                # ]

COL2_FEATURES = ['f0cedc0e2652404cb40d03109252961c', 'f623d290dcf54d858905e15a098bf300']


@pytest.fixture(params=FEATURE_URIS)
def feature(request):
    return request.param


def test_add_features(api, feature):
    b = api.add_features('col1', feature)
    c = api.get_features(collections='col1')
    assert len(list(c)) == 1
    assert b == c


@slow
def test_get_features_from_collection(api):
    c = api.get_features(collections='col2')
    assert len(list(c)) == 2
    for feature in COL2_FEATURES:
        assert feature in c


@slow
@pytest.mark.parametrize("service, expected, tolerance", [
    ('svc://nasa:srtm-3-arc-second', 14297, 1000),
    ('svc://nasa:srtm-30-arc-second', 27, 10),
    ('svc://ncdc:ghcn-daily', 100821, 1000),
    ('svc://ncdc:gsod', 28621, 1000),
    ('svc://noaa:coops-meteorological', 371, 50),
    ('svc://noaa:coops-water', 243, 50),
    ('svc://noaa:ndbc', 1117, 100),
    ('svc://usgs-ned:1-arc-second', 3619, 100),
    ('svc://usgs-ned:13-arc-second', 1240, 100),
    ('svc://usgs-ned:19-arc-second', 8358, 100),
    ('svc://usgs-ned:alaska-2-arc-second', 515, 50),
    ('svc://usgs-nlcd:2001', 203, 50),
    ('svc://usgs-nlcd:2006', 131, 50),
    ('svc://usgs-nlcd:2011', 203, 50),
    ('svc://usgs-nwis:dv', 35919, 1000),
    ('svc://usgs-nwis:iv', 15483, 1000),

])
def test_get_features_from_service(api, service, expected, tolerance):
    features = api.get_features(service)
    # assert number of features is within tolerance of expected
    assert abs(len(features) - expected) < tolerance


def test_new_feature(api):

    c = api.new_feature(collection='col3', display_name='NewFeat', geom_type='Point', geom_coords=[-94.2, 23.4])
    assert api.get_metadata(c)[c]['display_name'] == 'NewFeat'
    d = api.get_features(collections='col3')
    assert c in d


def test_update_feature(api):
    metadata = {'new_field': 'test'}

    c = api.update_metadata(COL2_FEATURES, display_name=['New Name', 'New Name'], metadata=metadata)
    for feature in COL2_FEATURES:
        assert c[feature]['display_name'] == 'New Name'
        assert c[feature]['metadata']['new_field'] == 'test'


def test_delete_features(api):
    c = api.new_feature(collection='col1', display_name='New', geom_type='Point', geom_coords=[-93.2, 21.4])
    d = api.new_feature(collection='col1', display_name='AnotherFeat', geom_type='Point',geom_coords=[-84.2, 22.4])
    api.delete(c)
    assert len(api.get_features(collections='col1')) == 1
    assert d in api.get_features(collections='col1')
