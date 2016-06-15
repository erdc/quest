import dsl
import os
import tempfile
import shutil

def _setup():
    path = os.path.dirname(os.path.realpath(__file__)) + '/files/example_base_dir'
    dsl.api.update_settings({'BASE_DIR': path})
    dsl.api.set_active_project('project2')


def _teardown():
    dsl.api.delete(dsl.api.get_collections())

def test_get_collections():
    _setup()
    dsl.api.set_active_project('project1')
    c = dsl.api.get_collections()
    assert len(list(c)) == 3

def test_new_collection():
    _setup()
    c = dsl.api.new_collection('test1')
    assert len(list(dsl.api.get_collections())) == 1
    metadata = {
        'display_name': 'my test collection',
        'tag': 'test tag'
    }
    c = dsl.api.new_collection('test2', metadata=metadata)
    assert len(list(dsl.api.get_collections())) == 2
    c = dsl.api.get_collections()
    assert 'test1' in c
    assert 'test2' in c
    _teardown()

def test_delete():
    _setup()
    dsl.api.new_collection('test1')
    dsl.api.new_collection('test2')
    dsl.api.new_collection('test3')

    dsl.api.delete('test2')
    assert len(list(dsl.api.get_collections())) == 2

    dsl.api.delete('test3')
    assert len(list(dsl.api.get_collections())) == 1
    _teardown()

def test_update_collection():
    _setup()
    dsl.api.new_collection('test1')
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = dsl.api.update_metadata('test1', metadata=metadata)
    assert c['test1']['display_name'] == 'New Name'
    assert c['test1']['new_field'] == 'test'
    _teardown()
