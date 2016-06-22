import pytest
import os
import shutil

import dsl

base_path = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(base_path, 'files/example_base_dir')


@pytest.fixture
def set_base_dir():
    dsl.api.update_settings({'BASE_DIR': BASE_DIR})
    return BASE_DIR



@pytest.fixture
def reset_projects_dir(set_base_dir, request):
    projects_dir = os.path.join(BASE_DIR, 'projects')

    def cleanup():
        shutil.rmtree(projects_dir, ignore_errors=True)

    cleanup()
    projects_template_dir = os.path.join(BASE_DIR, 'projects_template')
    shutil.copytree(projects_template_dir, projects_dir)

    request.addfinalizer(cleanup)

    metadata = {'NUMBER_OF_PROJECTS': 4}
    return metadata


@pytest.fixture
def set_active_project(set_base_dir, request):
    previous_active_project = dsl.api.get_active_project()
    tests_active_project = getattr(request.module, "ACTIVE_PROJECT", "default")
    dsl.api.set_active_project(tests_active_project)

    def teardown():
        dsl.api.set_active_project(previous_active_project)

    request.addfinalizer(teardown)


