"""Tests for functions in projects.py"""


import dsl
import tempfile


def test_get_projects():
    dsl.api.update_settings({'BASE_DIR': 'files/example_base_dir'})
    c = dsl.api.get_projects()
    assert len(list(c.keys())) == 2


def test_default_project():
    _setup()
    c = dsl.api.get_projects()
    assert len(list(c.keys())) == 1
    assert 'default' in c.keys()
    assert c['default']['display_name'] == 'Default Project'


def test_new_project():
    _setup()
    dsl.api.new_project('test')
    c = dsl.api.get_projects()
    assert len(list(c.keys())) == 2


def test_add_project():
    _setup()
    dsl.api.new_project('test1')
    dsl.api.new_project('test2')
    dsl.api.new_project('test3')
    dsl.api.delete_project('test2')
    dsl.api.delete_project('default')
    dsl.api.add_project('test4', 'test2')
    c = dsl.api.get_projects()
    assert len(list(c.keys())) == 3


def test_delete_project():
    _setup()
    dsl.api.new_project('test1')
    dsl.api.new_project('test2')
    dsl.api.new_project('test3')
    dsl.api.delete_project('test2')
    dsl.api.delete_project('default')
    c = dsl.api.get_projects()
    assert len(list(c.keys())) == 2


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
