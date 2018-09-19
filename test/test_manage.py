import pytest

from data import DATASET

ACTIVE_PROJECT = 'test_data'
COLLECTION = 'col2'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


@pytest.fixture
def add_collection(api, set_active_project):
    api.new_collection(COLLECTION)


def test_copy_dataset(api, add_collection, dataset_save_path):
    api.copy(DATASET, COLLECTION)


def test_move_dataset(api, add_collection, dataset_save_path):
    api.move(DATASET, COLLECTION)
