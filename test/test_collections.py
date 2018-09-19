import pytest

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


def test_get_collections(api):
    c = api.get_collections()
    assert len(list(c)) == 3


def test_new_collection(api):
    c = api.new_collection('test1')
    assert len(list(api.get_collections())) == 4
    metadata = {
        'display_name': 'my test collection',
        'tag': 'test tag'
    }
    c = api.new_collection('test2', metadata=metadata)
    assert len(list(api.get_collections())) == 5
    c = api.get_collections()
    assert 'test1' in c
    assert 'test2' in c


def test_delete(api):
    api.new_collection('test1')
    api.new_collection('test2')
    api.new_collection('test3')

    api.delete('test2')
    assert 5 == len(list(api.get_collections()))

    api.delete('test3')
    assert 4 == len(list(api.get_collections()))


def test_update_collection(api):
    api.new_collection('test1')
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = api.update_metadata('test1', metadata=metadata)
    assert c['test1']['metadata']['display_name'] == 'New Name'
    assert c['test1']['metadata']['new_field'] == 'test'
