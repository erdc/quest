"""Tests for functions in projects.py"""


import dsl
import tempfile
import os
import pytest
import shutil

ACTIVE_PROJECT = 'project1'

pytestmark = pytest.mark.usefixtures('reset_projects_dir')


@pytest.fixture()
def init_project_to_add(request):
    base_path = os.path.dirname(os.path.realpath(__file__))
    project_template_dir = os.path.join(base_path, 'files', 'project_to_add_template')
    project_dir = os.path.join(base_path, 'files', 'project_to_add')

    def handle_error(function, path, excinfo):
        print("Ignoring error", function, path, excinfo)

    def cleanup():
        shutil.rmtree(project_dir, ignore_errors=False, onerror=handle_error)
    cleanup()

    shutil.copytree(project_template_dir, project_dir)

    request.addfinalizer(cleanup)

    return project_dir


@pytest.fixture(params=['project1', 'default'])
def test_project(request):
    return request.param


def test_get_projects(reset_projects_dir):
    c = dsl.api.get_projects()
    assert len(c) == reset_projects_dir['NUMBER_OF_PROJECTS']


def test_default_project():
    c = dsl.api.get_projects()
    assert 'default' in c


def test_new_project(reset_projects_dir):
    dsl.api.new_project('test')
    c = dsl.api.get_projects()
    assert len(c) == reset_projects_dir['NUMBER_OF_PROJECTS'] + 1
    assert 'test' in c


def test_add_project(reset_projects_dir, init_project_to_add):
    added_project_name = 'added_test_project'
    dsl.api.add_project(added_project_name, init_project_to_add)
    c = dsl.api.get_projects()
    assert len(list(c)) == reset_projects_dir['NUMBER_OF_PROJECTS'] + 1
    assert added_project_name in c


def test_delete_project(reset_projects_dir, test_project):
    c = dsl.api.delete_project(test_project, True)
    assert len(c) == reset_projects_dir['NUMBER_OF_PROJECTS'] - 1
    assert test_project not in c

    # test that 'default' gets restored after delete on get_projects
    c = dsl.api.get_projects()
    if test_project == 'default':
        assert len(c) == reset_projects_dir['NUMBER_OF_PROJECTS']
        assert test_project in c
    else:
        assert len(c) == reset_projects_dir['NUMBER_OF_PROJECTS'] - 1
        assert test_project not in c


def test_set_active_project(set_active_project):
    assert dsl.api.get_active_project() == 'project1'
    dsl.api.set_active_project('project2')
    assert dsl.api.get_active_project() == 'project2'
