"""API functions related to Collections."""
from __future__ import print_function
import datetime
from jsonrpc import dispatcher
from .. import util
from .projects import get_active_project, get_projects
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
def get_collections():
    """Get available collections.

    Collections are folders on the local disk that contain downloaded or created data
    along with associated metadata.

    Returns
    -------
    collections (dict): Available collections keyed by the collection name
    """

    collections = {}
    for name in _load_collections():
        metadata = _load_collection(name).get('metadata', {})
        metadata['_name_'] = name
        collections[name] = metadata

    return collections


@dispatcher.add_method
def new_collection(name, display_name=None, description=None, metadata=None):
    """Create a new collection.

    Create a new collection by creating a new folder and placing a yaml
    file in the folder for dsl metadata and adding a reference to the
    master collections metadata folder.

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
    collections.append(name)
    _write_collections(collections)

    metadata.update({
        '_type_': 'collection',
        '_display_name_': display_name,
        '_description_': description,
        '_created_on_': datetime.datetime.now().isoformat(),
    })

    collection = {'metadata': metadata}
    _write_collection(name, collection)

    return collection


@dispatcher.add_method
def update_collection(name, display_name=None, description=None, metadata=None):
    """Update metadata of collection."""
    c = _load_collection(name)

    if display_name is not None:
        c['metadata'].update({'_display_name_': display_name})

    if description is not None:
        c['metadata'].update({'_description_': description})

    if metadata is not None:
        c['metadata'].update(metadata)

    _write_collection(name, c['metadata'])
    return c


@dispatcher.add_method
def delete_collection(name, delete_data=True):
    """delete a collection.

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


def _collection_features_file(collection):
    collection = _load_collections().get(collection)
    if collection is None:
        raise ValueError('Collection Not Found')

    folder = collection['folder']
    path = os.path.join(_get_collections_dir(), folder)

    return os.path.join(path, 'features.h5')


def _collection_db(collection):
    collection = _load_collections().get(collection)
    if collection is None:
        raise ValueError('Collection Not Found')

    folder = collection['folder']
    path = os.path.join(_get_collections_dir(), folder)

    return os.path.join(path, 'dsl.db')


def _read_collection_features(collection):
    features_file = _collection_features_file(collection)
    try:
        features = pd.read_hdf(features_file, 'table')
    except:
        features = pd.DataFrame()
    return features


def _write_collection_features(collection, features):
    features_file = _collection_features_file(collection)
    features.to_hdf(features_file, 'table')


def _get_collection_file(name):
    collections = _load_collections()
    if name not in collections:
        raise ValueError('Collection %s not found' % name)

    return os.path.join(_get_project_dir(), name, 'dsl.yml')


def _get_project_dir():
    return get_projects()[get_active_project()]['_folder_']


def _get_collections_index_file():
    return os.path.join(_get_project_dir(), 'dsl.yml')


def _load_collection(name):
    """load collection."""
    path = _get_collection_file(name)
    return util.read_yaml(path)


def _load_collections():
    """load list of collections."""
    path = _get_collections_index_file()
    collections = util.read_yaml(path).get('collections')
    if collections is None:
        return []

    return collections


def _write_collection(name, collection):
    """write collection."""
    util.write_yaml(_get_collection_file(name), collection)


def _write_collections(collections):
    """write list of collections to file."""
    path = _get_collections_index_file()
    contents = util.read_yaml(path)
    contents.update({'collections': collections})
    util.write_yaml(path, contents)
