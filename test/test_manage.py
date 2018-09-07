import pytest
import os

from data import DATASET

ACTIVE_PROJECT = 'test_data'
COLLECTION = 'col2'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


@pytest.fixture
def add_collection(api, set_active_project):
    api.new_collection(COLLECTION)


@pytest.fixture
def dataset_file_path(api, reset_projects_dir):
    save_path = os.path.join(reset_projects_dir['BASE_DIR'],
                             'projects/test_data/col1/usgs-nwis/iv/d43d503dc792475bb322ef71ffb885bd/d43d503dc792475bb322ef71ffb885bd.h5')
    api.update_metadata(uris=DATASET, quest_metadata={'file_path': save_path})

    return save_path


def test_copy_dataset(api, add_collection, dataset_file_path):
    api.copy(DATASET, COLLECTION)


def test_move_dataset(api, add_collection, dataset_file_path):
    api.move(DATASET, COLLECTION)
