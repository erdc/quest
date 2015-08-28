import dsl
import os
import tempfile
import shutil


def test_get_collections():
    dsl.api.update_settings({'BASE_DIR': 'files'})
    c = dsl.api.get_collections()
    assert len(c.keys()) == 3


def test_new_collection():
    _setup()
    c = dsl.api.new_collection()
    assert len(dsl.api.get_collections().keys()) == 4

    collection_dir = tempfile.mkdtemp()
    c = dsl.api.new_collection({
                            'display_name': 'my test collection', 
                            'tag': 'test tag'
                        }, 
                        path=collection_dir)

    assert len(dsl.api.get_collections().keys()) == 5
    assert c.values()[0] == {
                        'display_name': 'my test collection', 
                        'tag': 'test tag', 
                        'path': os.path.join(collection_dir, c.keys()[0]),
                    }


def test_delete_collection():
    _setup()
    dsl.api.delete_collection('bad-uid')
    assert len(dsl.api.get_collections().keys()) == 3

    dsl.api.delete_collection('345b35ada1de41159ced46e8eb880960')
    assert len(dsl.api.get_collections().keys()) == 2


def test_update_collection():
    _setup()
    metadata = {'display_name': 'New Name', 'new_field': 'test'}
    
    c = dsl.api.update_collection('bad-uid', metadata)
    assert c == {}

    c = dsl.api.update_collection('345b35ada1de41159ced46e8eb880960', metadata)
    assert c['display_name'] == 'New Name'
    assert c['new_field'] == 'test'


def _setup():
    tmpdir = tempfile.mkdtemp()
    shutil.copyfile('files/dsl_collections.yml', os.path.join(tmpdir, 'dsl_collections.yml'))
    dsl.api.update_settings({'BASE_DIR': tmpdir})
    return tmpdir