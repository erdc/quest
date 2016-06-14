"""Tests for functions in projects.py"""


import dsl
import tempfile
import os


def _setup():
    path = os.path.dirname(os.path.realpath(__file__)) + '/files/example_base_dir'
    dsl.api.update_settings({'BASE_DIR': path})
    dsl.api.set_active_project('project1')

def _teardown(uri):
    dsl.api.delete_project(uri,True)

def test_get_projects():
    _setup()
    c = dsl.api.get_projects()
    assert len(c) == 3
#
def test_default_project():
    _setup()
    c = dsl.api.get_projects()
    assert 'default' in c


def test_new_project():
    _setup()
    dsl.api.new_project('test')
    c = dsl.api.get_projects()
    assert len(c) == 4
    _teardown('test')
#
#
def test_add_project():
    _setup()
    path=os.getcwd()
    dsl.api.add_project('added_test', path+'/test/files/sample_project_dir/projects/addedTest')
    c = dsl.api.get_projects()
    assert len(list(c)) == 4
    _teardown('added_test')

def test_delete_project():
    _setup()
    dsl.api.new_project('test_project')
    c = dsl.api.get_projects()
    assert len(c) == 4
    dsl.api.delete_project('test_project')
    c=dsl.api.get_projects()
    assert len(c) == 3
    _teardown('test_project')


def test_set_active_project():
    _setup()
    assert dsl.api.get_active_project() == 'project1'
    dsl.api.new_project('test1')
    dsl.api.set_active_project('test1')
    assert dsl.api.get_active_project() == 'test1'
    _teardown('test1')

