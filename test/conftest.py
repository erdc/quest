import pytest
import os
import shutil

import dsl

base_path = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(base_path, 'files/example_base_dir')


@pytest.fixture(scope='session')
def save_settings(request):
    previous_settings = {}
    # updating settings like this is required so pytest doesn't override the variable when the finalizer is called
    previous_settings.update(dsl.api.get_settings())

    def restore_settings():
        dsl.api.update_settings(previous_settings)
        dsl.api.save_settings()

    request.addfinalizer(restore_settings)


@pytest.fixture
def reset_settings():
    test_settings = {'BASE_DIR': BASE_DIR,
                     'CACHE_DIR': 'cache',
                     'PROJECTS_DIR': 'projects',
                     'USER_SERVICES': []
                     }

    dsl.api.update_settings(test_settings)
    return BASE_DIR


@pytest.fixture
def reset_projects_dir(reset_settings, request):
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
def set_active_project(reset_settings, request):
    previous_active_project = dsl.api.get_active_project()
    tests_active_project = getattr(request.module, "ACTIVE_PROJECT", "default")
    dsl.api.set_active_project(tests_active_project)

    def teardown():
        dsl.api.set_active_project(previous_active_project)

    request.addfinalizer(teardown)


