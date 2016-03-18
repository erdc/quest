"""API functions related to Collections."""
from __future__ import print_function
import datetime
from jsonrpc import dispatcher
from .. import util
from . import db
from .projects import get_active_project, get_projects, active_db
import os
import pandas as pd
import shutil


@dispatcher.add_method
def delete_from_collection(collection, uris):
    """Remove uris from collection.

    TODO
    """
    uris = util.listify(uris)
    for uri in uris:
        _delete_from_collection(collection, uri)

    return


@dispatcher.add_method
def get_collections(metadata=None):
    """Get available collections.

    Collections are folders on the local disk that contain downloaded or created data
    along with associated metadata.

    args:
        metadata (bool, optional):
            Optionally return collection metadata

    Returns
    -------
    collections (list or dict):
        Available collections
    """

    collections = _load_collections()
    collections = {k: util.to_metadata(v) for k, v in collections.items()}
    if not metadata:
        collections = collections.keys()

    return collections


@dispatcher.add_method
def new_collection(name, display_name=None, description=None, metadata=None):
    """Create a new collection.

    Create a new collection by creating a new folder in project directory
    and adding collection metadata in project database.

    Args:
        name (string): name of the collection used in all dsl function calls,
            must be unique. Will also be the folder name of the collection.
        display_name (string, optional): Display name for collection.
        description (string, optional): Description of collection.
        metadata (dict, optional): user defined metadata

    Returns:
        A dict representing the collection keyed on name
    """
    name = name.lower()
    collections = _load_collections()
    if name in collections:
        raise ValueError('Collection %s already exists' % name)

    if display_name is None:
        display_name = name

    if description is None:
        description = ''

    if metadata is None:
        metadata = {}

    path = os.path.join(_get_project_dir(), name)
    util.mkdir_if_doesnt_exist(path)

    dsl_metadata = {
        'type': 'collection',
        'display_name': display_name,
        'description': description,
        'created_on': datetime.datetime.now().isoformat(),
    }
    db.upsert(active_db(), 'collections', name, dsl_metadata, metadata)
    return _load_collection(name)


@dispatcher.add_method
def update_collection(name, display_name=None, description=None, metadata=None):
    """Update metadata of collection.

    TODO - REPLACE WITH GENERIC UPDATE METADATA CALL
    """
    c = _load_collection(name)

    if display_name is not None:
        c['metadata'].update({'_display_name': display_name})

    if description is not None:
        c['metadata'].update({'_description': description})

    if metadata is not None:
        c['metadata'].update(metadata)

    db.upsert(active_db(), 'collections', name, dsl_metadata, metadata)
    return c


@dispatcher.add_method
def delete_collection(name, delete_data=True):
    """delete a collection.

    TODO FIX THIS TO WORK WITH DB

    Deletes a collection from the collections metadata file.
    Optionally deletes all data under collection.

    Parameters
    ----------
        name : str,
            The name of the collection

        delete_data : bool,
            if True all data in the collection will be deleted

        Returns
        -------
        collections : dict,
            A python dict representation of the list of available collections,
            the updated collections list is also written to a json file.
    """
    collections = _load_collections()

    if name not in collections:
        raise ValueError('Collection %s not found' % name)

    if delete_data:
        path = os.path.join(_get_project_dir(), name)
        if os.path.exists(path):
            print('deleting all data under path:', path)
            shutil.rmtree(path)

    print('removing %s from collections' % name)
    collections.remove(name)
    _write_collections(collections)
    return collections


def _read_collection_features(collection):
    """
    TODO REPLACE WITH GENERIC GET FEATURES
    """
    features_file = _collection_features_file(collection)
    try:
        features = pd.read_hdf(features_file, 'table')
    except:
        features = pd.DataFrame()
    return features


def _write_collection_features(collection, features):
    """
    TODO MAKE WORK WITH DB
    """
    features = _collection_features_file(collection)
    features.to_hdf(features_file, 'table')


def _get_project_dir():
    return get_projects(metadata=True)[get_active_project()]['folder']


def _load_collection(name):
    """load collection."""
    return db.read_data(active_db(), 'collections', name)


def _load_collections():
    """load list of collections."""
    return db.read_all(active_db(), 'collections')
