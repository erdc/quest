import dsl
import os
import pytest

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')

FEATURE_URIS = [
                'svc://usgs-ned:19-arc-second/581d2561e4b08da350d5a3b2',
                'svc://ncdc:gsod/028140-99999',
                'svc://usgs-nwis:iv/01529950',
                ]

COL2_FEATURES =['f0cedc0e2652404cb40d03109252961c', 'f623d290dcf54d858905e15a098bf300']




@pytest.fixture(params=FEATURE_URIS)
def feature(request):
    return request.param


# def test_add_features(feature):
#     b = dsl.api.add_features('col1', feature)
#     c = dsl.api.get_features(collections='col1')
#     assert len(list(c)) == 1
#     assert b == c



def test_get_features():
    c = dsl.api.get_features(collections='col2')
    assert len(list(c)) == 2
    for feature in COL2_FEATURES:
        assert feature in c
#

def test_new_feature():

    c = dsl.api.new_feature(collection='col3', display_name='NewFeat', geom_type='Point', geom_coords=[-94.2, 23.4])
    assert dsl.api.get_metadata(c)[c]['display_name'] == 'NewFeat'
    d = dsl.api.get_features(collections='col3')
    assert c in d


def test_update_feature():
    metadata = {'new_field': 'test'}

    c = dsl.api.update_metadata(COL2_FEATURES, display_name=['New Name', 'New Name'], metadata=metadata)
    print(c)
    for feature in COL2_FEATURES:
        assert c[feature]['display_name'] == 'New Name'
        assert c[feature]['metadata']['new_field'] == 'test'

#
def test_delete_features():
    c = dsl.api.new_feature(collection='col1', display_name='New', geom_type='Point', geom_coords=[-93.2, 21.4])
    d = dsl.api.new_feature(collection='col1', display_name='AnotherFeat', geom_type='Point',geom_coords=[-84.2, 22.4])
    dsl.api.delete(c)
    assert len(dsl.api.get_features(collections='col1')) == 1
    assert d in dsl.api.get_features(collections='col1')
