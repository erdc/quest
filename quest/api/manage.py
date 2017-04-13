"""API functions related to deleting resources.

delete, move, and copy fn for collections/features/datasets
"""

from jsonrpc import dispatcher
import os
import shutil
from ..util.log import logger


from .features import get_features, add_features
from .datasets import get_datasets
from .database import get_db, db_session
from .projects import _get_project_dir
from .collections import get_collections
from .metadata import get_metadata, update_metadata
from .. import util


@dispatcher.add_method
def delete(uris):
    """Delete metadata for resource(s)

    WARNING:
        deleting a feature deletes all associated datasets
        deleting a collection deletes all associated features and datasets
        TODO deleting dataset files/folders

    Args:
        uris (string, comma separated string or list of strings, Required):
            uri(s) of collection, feature, and/or service to delete

    Returns:
        status (bool):
            True on success

    """
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=['services'], require_same_type=True)
    resource = list(grouped_uris)[0]
    uris = grouped_uris[resource]

    db = get_db()
    for uri in uris:
        if resource == 'collections':
            if uri not in get_collections():
                logger.error('Collection does not exist: %s', uri)
                raise ValueError('Collection does not exists')

            # delete all datasets and all features and folder
            features = get_features(collections=uri)
            delete(features)
            with db_session:
                db.Collection[uri].delete()

            path = _get_project_dir()
            path = os.path.join(path, uri)
            if os.path.exists(path):
                logger.info('deleting all data under path: %s' % path)
                shutil.rmtree(path)

        if resource == 'features':
            # delete feature and associated datasets
            datasets = get_datasets(filters={'feature': uri})
            delete(datasets)

            with db_session:
                db.Feature[uri].delete()

        if resource == 'datasets':
            # delete dataset and associated dataset files
            with db_session:
                db.Dataset[uri].delete()
            # TODO delete data files/folders

    return True


@dispatcher.add_method
def move(uris, destination_collection):
    """Move feature/dataset from one collection to another.

    Args:
        uris (string or list of strings, Required):
            uris of features/datasets to move
        destination_collection (string):
            collection name
    Returns:
        status (bool):
            True on success
    """

    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    grouped_uris = util.classify_uris(uris, as_dataframe=False,
                                      exclude=['services', 'collections'], require_same_type=True)
    resource = list(grouped_uris)[0]
    uris = grouped_uris[resource]

    project_path = _get_project_dir()
    destination_collection_path = os.path.join(project_path, destination_collection)

    for uri in uris:
        if resource == 'features':
            feature_metadata = get_metadata(uri)[uri]

            collection_path = os.path.join(project_path, feature_metadata['collection'])

            datasets = get_datasets(expand=True, filters={'feature': uri})
            for dataset_name, dataset_metadata in datasets.items():
                _move_dataset(dataset_metadata, collection_path, destination_collection_path, uri)

            update_metadata(uri, quest_metadata={'collection': destination_collection})

        if resource == 'datasets':
            dataset_metadata = get_metadata(uri)[uri]

            collection_path = os.path.join(project_path, dataset_metadata['collection'])

            feature = dataset_metadata['feature']

            new_feature = add_features(destination_collection, feature)[0]

            _move_dataset(dataset_metadata, collection_path, destination_collection_path, new_feature)

    return True


@dispatcher.add_method
def copy(uris, destination_collection):
    """Copy feature/dataset from one collection to another.

       Args:
           uris (string or list of strings, Required):
               uris of features/datasets to copy
           destination_collection (string):
               collection name
       Returns:
           status (bool):
               True on success
       """
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    grouped_uris = util.classify_uris(uris, as_dataframe=False,
                                      exclude=['services', 'collections'], require_same_type=True)
    resource = list(grouped_uris)[0]
    uris = grouped_uris[resource]

    project_path = _get_project_dir()
    destination_collection_path = os.path.join(project_path, destination_collection)

    for uri in uris:
        if resource == 'collections':
            pass
            # if destination collection exists:
            #   copy all features from collection to destination

        if resource == 'features':
            feature_metadata = get_metadata(uri)[uri]

            collection_path = os.path.join(project_path, feature_metadata['collection'])

            new_feature = add_features(destination_collection, uri)[0]

            datasets = get_datasets(expand=True, filters={'feature': uri})
            for dataset_name, dataset_metadata in datasets.items():
                _copy_dataset(dataset_metadata, collection_path, destination_collection_path, new_feature)

        if resource == 'datasets':
            dataset_metadata = get_metadata(uri)[uri]

            collection_path = os.path.join(project_path, feature_metadata['collection'])

            feature = dataset_metadata['feature']

            new_feature = add_features(destination_collection, feature)[0]

            _copy_dataset(dataset_metadata, collection_path, destination_collection_path, new_feature)

    return True


def _copy_dataset(dataset_metadata, collection_path, destination_collection_path, feature):
    _update_dataset_file_location(shutil.copy2, dataset_metadata, collection_path, destination_collection_path, feature)


def _move_dataset(dataset_metadata, collection_path, destination_collection_path, feature):
    _update_dataset_file_location(shutil.move, dataset_metadata, collection_path, destination_collection_path, feature)


def _update_dataset_file_location(func, dataset_metadata, collection_path, destination_collection_path, feature):
    quest_metadata = {'feature': feature}
    file_path = dataset_metadata['file_path']
    if file_path is not None:
        rel_path = os.path.relpath(file_path, collection_path)
        new_file_path = os.path.normpath(os.path.join(destination_collection_path, rel_path))
        quest_metadata['file_path'] = new_file_path

        util.mkdir_if_doesnt_exist(os.path.split(new_file_path)[0])
        func(file_path, new_file_path)

    update_metadata(dataset_metadata['name'], quest_metadata=quest_metadata)
