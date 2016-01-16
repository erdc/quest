import dsl
import os
import tempfile
import shutil


def test_get_collections():
    dsl.api.update_settings({'BASE_DIR': 'files/example_base_dir'})
    c = dsl.api.get_collections()
    assert len(list(c.keys())) == 3


def test_new_collection():
    _setup()
    c = dsl.api.new_collection('test1')
    assert len(list(dsl.api.get_collections().keys())) == 1

    collection_dir = tempfile.mkdtemp()
    c = dsl.api.new_collection('test2', {
                                        'display_name': 'my test collection',
                                        'tag': 'test tag'
                                },
                                folder=collection_dir)

    assert len(list(dsl.api.get_collections().keys())) == 2
    c = dsl.api.get_collections()
    assert 'test1' in c.keys()
    assert 'test2' in c.keys()
    assert c['test2']['folder'] == collection_dir


def test_delete_collection():
    _setup()
    dsl.api.new_collection('test1')
    dsl.api.new_collection('test2')
    dsl.api.new_collection('test3')

    dsl.api.delete_collection('test2')
    assert len(list(dsl.api.get_collections().keys())) == 2

    dsl.api.delete_collection('test3')
    assert len(list(dsl.api.get_collections().keys())) == 1


def test_update_collection():
    _setup()
    dsl.api.new_collection('test1')
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = dsl.api.update_collection('test1', metadata)
    assert c['display_name'] == 'New Name'
    assert c['new_field'] == 'test'


def _setup():
    tmpdir = tempfile.mkdtemp()
    c = dsl.api.get_projects()
    dsl.api.update_settings({'BASE_DIR': tmpdir})
    return tmpdir
