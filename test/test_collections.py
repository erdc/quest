import quest
import pytest

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


def test_get_collections():
    c = quest.api.get_collections()
    assert len(list(c)) == 3


def test_new_collection():
    c = quest.api.new_collection('test1')
    assert len(list(quest.api.get_collections())) == 4
    metadata = {
        'display_name': 'my test collection',
        'tag': 'test tag'
    }
    c = quest.api.new_collection('test2', metadata=metadata)
    assert len(list(quest.api.get_collections())) == 5
    c = quest.api.get_collections()
    assert 'test1' in c
    assert 'test2' in c


def test_delete():
    quest.api.new_collection('test1')
    quest.api.new_collection('test2')
    quest.api.new_collection('test3')

    quest.api.delete('test2')
    assert len(list(quest.api.get_collections())) == 5

    quest.api.delete('test3')
    assert len(list(quest.api.get_collections())) == 4


def test_update_collection():
    quest.api.new_collection('test1')
    metadata = {'display_name': 'New Name', 'new_field': 'test'}

    c = quest.api.update_metadata('test1', metadata=metadata)
    assert c['test1']['metadata']['display_name'] == 'New Name'
    assert c['test1']['metadata']['new_field'] == 'test'
