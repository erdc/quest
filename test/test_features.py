import dsl


def _setup():
    dsl.api.update_settings({'BASE_DIR': 'files/example_base_dir'})

def _teardown(uri):
    dsl.api.delete(uri)
    dsl.api.new_collection(uri)

def test_add_features():
    _setup()
    b = dsl.api.add_features('col1', 'svc://usgs-ned:19-arc-second/53174780e4b0cd4cd83bf20e')
    c = dsl.api.get_features(collections='col1')
    assert len(list(c)) == 1
    assert b == c
    _teardown('col1')

def test_get_features():
    _setup()
    dsl.api.add_features(collection='col2', features='svc://usgs-nwis:iv/01529500, svc://usgs-nwis:iv/01529950')
    c=dsl.api.get_features(collections='col2')
    assert len(list(c)) == 2
    _teardown('col2')

def test_new_feature():
    _setup()
    c = dsl.api.new_feature(collection='col3', display_name='NewFeat', geom_type='LineString')
    assert dsl.api.get_metadata(c)[c]['_display_name'] == 'NewFeat'
    assert c in dsl.api.get_features(collections='col3')
    _teardown('col3')

def test_update_feature():
     _setup()
     assert dsl.api.get_metadata('col2')['col2']['_description'] == None
     dsl.api.update_metadata('col2', description='test collection2')
     assert dsl.api.get_metadata('col2')['col2']['_description'] == "['test collection2']"
     _teardown('col2')


def test_delete_features():
    _setup()
    c = dsl.api.new_feature(collection='col1', display_name='New')
    d = dsl.api.new_feature(collection='col1', display_name='AnotherFeat')
    dsl.api.delete(c)
    assert len(dsl.api.get_features(collections='col1')) == 1
    assert d in dsl.api.get_features(collections='col1')
    _teardown('col1')