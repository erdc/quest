import dsl
import os
import tempfile
import shutil


def test_get_collections():
    dsl.api.update_settings({'BASE_DIR': 'files/example_base_dir'})
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

def test_delete():
    _setup()
    dsl.api.new_collection('test1')
    dsl.api.new_collection('test2')
    dsl.api.new_collection('test3')

    dsl.api.delete('test2')
    assert len(list(dsl.api.get_collections())) == 2

    dsl.api.delete('test3')
    assert len(list(dsl.api.get_collections())) == 1


def test_update_collection():
    _setup()
    dsl.api.new_collection('test1')
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = dsl.api.update_metadata('test1', metadata=metadata)
    assert c['test1']['display_name'] == 'New Name'
    assert c['test1']['new_field'] == 'test'


def _setup():
    tmpdir = tempfile.mkdtemp()
    c = dsl.api.get_projects()
    dsl.api.update_settings({'BASE_DIR': tmpdir})
    return tmpdir
