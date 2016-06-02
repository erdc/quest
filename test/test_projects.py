"""Tests for functions in projects.py"""


import dsl
import tempfile
import os





def test_get_projects():
    dsl.api.update_settings({'BASE_DIR': 'files/example_base_dir'})
    c = dsl.api.get_projects()
    assert len(list(c)) == 2


def test_default_project():
    _setup()
    c = dsl.api.get_projects()
    assert len(list(c)) == 1
    assert 'default' in c
    #assert c['default']['display_name'] == 'Default Project'


def test_new_project():
    _setup()
    dsl.api.new_project('test')
    c = dsl.api.get_projects()
    assert len(list(c)) == 2


def test_add_project():
    _setup()
    dsl.api.new_project('test1')
    dsl.api.new_project('test2')
    dsl.api.new_project('test3')
    dsl.api.delete_project('test2')
    dsl.api.delete_project('default')
    path=os.getcwd()
    dsl.api.add_project('project1', path+'/files/example_base_dir/projects/project1')
    c = dsl.api.get_projects()
    assert len(list(c)) == 3


def test_delete_project():
    _setup()
    dsl.api.new_project('test1')
    dsl.api.new_project('test2')
    dsl.api.new_project('test3')
    dsl.api.delete_project('test2')
    dsl.api.delete_project('default')
    c = dsl.api.get_projects()
    assert len(list(c)) == 2


def set_active_project():
    _setup()
    assert dsl.api.get_active_project() == 'default'
    dsl.api.new_project('test1')
    dsl.api.set_active_project('test1')
    assert dsl.api.get_active_project() == 'test1'


def _setup():
    tmpdir = tempfile.mkdtemp()
    dsl.api.update_settings({'BASE_DIR': tmpdir})
    return tmpdir
