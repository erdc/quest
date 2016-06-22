import dsl
import os
import pytest

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


def test_add_features():
    b = dsl.api.add_features('col1', 'svc://usgs-ned:19-arc-second/53174780e4b0cd4cd83bf20e')
    c = dsl.api.get_features(collections='col1')
    assert len(list(c)) == 1
    assert b == c


def test_get_features():
    dsl.api.add_features(collection='col2', features='svc://usgs-nwis:iv/01529500, svc://usgs-nwis:iv/01529950')
    c=dsl.api.get_features(collections='col2')
    assert len(list(c)) == 2


def test_new_feature():
    c = dsl.api.new_feature(collection='col3', display_name='NewFeat', geom_type='LineString')
    assert dsl.api.get_metadata(c)[c]['_display_name'] == 'NewFeat'
    assert c in dsl.api.get_features(collections='col3')


def test_update_feature():
    dsl.api.update_metadata('col2', description='test collection2')
    assert dsl.api.get_metadata('col2')['col2']['_description'] == "['test collection2']"
    dsl.api.update_metadata('col2', description='test_collection2_sample')
    assert dsl.api.get_metadata('col2')['col2']['_description'] == "['test_collection2_sample']"


def test_delete_features():
    c = dsl.api.new_feature(collection='col1', display_name='New')
    d = dsl.api.new_feature(collection='col1', display_name='AnotherFeat')
    dsl.api.delete(c)
    assert len(dsl.api.get_features(collections='col1')) == 1
    assert d in dsl.api.get_features(collections='col1')
