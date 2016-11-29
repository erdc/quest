"""API functions related to deleting resources.

delete fn for collections/features/datasets
"""

from jsonrpc import dispatcher
import pandas as pd
import os
import shutil

from .projects import active_db
from .features import get_features
from .datasets import get_datasets
from .. import util
from . import db

from .metadata import get_metadata, update_metadata
from ..util import mkdir_if_doesnt_exist


@dispatcher.add_method
def delete(uris):
    """Update metadata for resource(s)

    WARNING:
        deleting a feature deletes all associated datasets
        deleting a collection deletes all associated features and datasets
        TODO deleting dataset files/folders

    Args:
        uris (string, comma separated string, list of strings):
            list of uris to update metadata for.
        delete_data (bool, optional): delete associated data

    Returns:
        status (bool): True on success
    """
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    df = util.classify_uris(uris)
    uris = util.listify(uris)
    resource = pd.unique(df['type']).tolist()

    if len(resource) > 1:
        raise ValueError('All uris must be of the same type')

    resource = resource[0]
    if resource == 'service':
        raise ValueError('Service uris cannot be deleted')

    for uri in uris:
        if resource == 'collections':
            # delete all datasets and all features and folder
            features = get_features(collections=uri)
            delete(features)
            db.delete(active_db(), 'collections', uri)
            path = os.path.split(active_db())[0]
            path = os.path.join(path, uri)
            if os.path.exists(path):
                print('deleting all data under path: %s' % path)
                shutil.rmtree(path)

        if resource == 'features':
            # delete feature and associated datasets
            datasets = get_datasets(filters={'feature': uri})
            delete(datasets)
            db.delete(active_db(), 'features', uri)

        if resource == 'datasets':
            # delete dataset and associated dataset files
            db.delete(active_db(), 'datasets', uri)
            # TODO delete data files/folders

    return True


@dispatcher.add_method
def move(uris, destination_collection):
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    df = util.classify_uris(uris)
    uris = util.listify(uris)
    resource = pd.unique(df['type']).tolist()

    if len(resource) > 1:
        raise ValueError('All uris must be of the same type')

    resource = resource[0]
    if resource == 'service':
        raise ValueError('Service uris cannot be moved')
    elif resource == 'collections':
        raise ValueError('Collections cannot be moved')

    for uri in uris:
        if resource == 'features':
            feature_metadata = get_metadata(uri)[uri]

            project_path = os.path.split(active_db())[0]
            collection_path = os.path.join(project_path, feature_metadata['_collection'])
            destination_collection_path = os.path.join(project_path, destination_collection)

            datasets = get_datasets(metadata=True, filters={'feature': uri})
            for dataset_name, dataset in datasets.items():
                _move_dataset(dataset, collection_path, destination_collection_path, destination_collection)

            update_metadata(uri, dsl_metadata={'collection': destination_collection})

        if resource == 'datasets':
            dataset = get_metadata(uri)[uri]

            project_path = os.path.split(active_db())[0]
            collection_path = os.path.join(project_path, dataset['_collection'])
            destination_collection_path = os.path.join(project_path, destination_collection)

            _move_dataset(dataset, collection_path, destination_collection_path, destination_collection)

    return True


def _move_dataset(dataset, collection_path, destination_collection_path, destination_collection):
    save_path = dataset['_save_path']
    rel_path = os.path.relpath(save_path, collection_path)
    new_save_path = os.path.normpath(os.path.join(destination_collection_path, rel_path))

    mkdir_if_doesnt_exist(os.path.split(new_save_path)[0])
    shutil.move(save_path, new_save_path)

    update_metadata(dataset['_name'], dsl_metadata={'save_path': new_save_path, 'collection': destination_collection})



@dispatcher.add_method
def copy(uris, destination_collection):
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    df = util.classify_uris(uris)
    uris = util.listify(uris)
    resource = pd.unique(df['type']).tolist()

    if len(resource) > 1:
        raise ValueError('All uris must be of the same type')

    resource = resource[0]
    if resource == 'service':
        raise ValueError('Service uris cannot be moved')

    for uri in uris:
        if resource == 'collections':
            process_collections(uri)

        if resource == 'features':
            process_features(uri)

        if resource == 'datasets':
            process_datasets(uri)

    return True