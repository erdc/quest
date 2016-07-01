import dsl
import os
import pytest

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')

FEATURE_URIS = [
                'svc://usgs-ned:19-arc-second/53174780e4b0cd4cd83bf20e',
                'svc://ncdc:gsod/028140-99999',
                # 'svc://usgs-nwis:iv/01529950',  # TODO: Doesn't work in Python 3
                ]

COL2_FEATURES = ['fa221501cb8348bea19239827796233a', 'f05e841ddc4b457abafad38580ecb8ca']


@pytest.fixture(params=FEATURE_URIS)
def feature(request):
    return request.param


def test_add_features(feature):
    b = dsl.api.add_features('col1', feature)
    c = dsl.api.get_features(collections='col1')
    assert len(list(c)) == 1
    assert b == c


def test_get_features():
    c = dsl.api.get_features(collections='col2')
    assert len(list(c)) == 2
    for feature in COL2_FEATURES:
        assert feature in c


def test_new_feature():
    c = dsl.api.new_feature(collection='col3', display_name='NewFeat', geom_type='LineString')
    assert dsl.api.get_metadata(c)[c]['_display_name'] == 'NewFeat'
    assert c in dsl.api.get_features(collections='col3')


def test_update_feature():
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = dsl.api.update_metadata(COL2_FEATURES, metadata=metadata)
    for feature in COL2_FEATURES:
        assert c[feature]['display_name'] == 'New Name'
        assert c[feature]['new_field'] == 'test'


def test_delete_features():
    c = dsl.api.new_feature(collection='col1', display_name='New')
    d = dsl.api.new_feature(collection='col1', display_name='AnotherFeat')
    dsl.api.delete(c)
    assert len(dsl.api.get_features(collections='col1')) == 1
    assert d in dsl.api.get_features(collections='col1')
