"""API functions related to Collections

"""
from __future__ import print_function
import datetime
from jsonrpc import dispatcher
from .. import util
import os
import pandas as pd
import shutil
import yaml


COLLECTION_METADATA_FILE = 'dsl.yml'


@dispatcher.add_method
def delete_from_collection(collection, uris):
    """Remove uris from collection

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
    collections (dict): Available collections keyed by the collection uid  
    """
    collections = {}
    for uid, collection in _load_collections().iteritems():
        folder = collection['folder']
        path = os.path.join(util.get_data_dir(), folder)

        metadata = _load_collection(uid)['metadata']
        metadata.update({
            'uid': uid,
            'folder': path,
        })
        collections[uid] = metadata
    return collections


@dispatcher.add_method     
def new_collection(uid, display_name=None, metadata={}, folder=None):
    """Create a new collection

    Create a new collection by creating a new folder and placing a yaml
    file in the folder for dsl metadata and adding a reference to the 
    master collections metadata folder.

    Args:
        uid (string): uid of the collection used in all dsl function calls,
            must be unique.
        display_name (string, optional): Display name for collection, default is uid
        metadata (dict, optional): metadata values, difault is empty dict
        folder (string, optional): folder in which to save collection, default is a folder 
            named the same as the uid

    Returns:
        A dict representing the collection keyed on uid
    """

    uid = uid.lower()
    collections = _load_collections()
    if uid in collections.keys():
        raise ValueError('Collection %s already exists, please use a unique name', uid)

    if folder is None:
        folder = uid
    
    path = os.path.join(util.get_data_dir(), folder)
    util.mkdir_if_doesnt_exist(path)
    collections.update({uid: {'folder': folder}})
    _write_collections(collections)
    
    metadata.update({
        'display_name': metadata.get('display_name', uid),
        'description': metadata.get('description', None),
        'created_on': datetime.datetime.now().isoformat(),
    })
    collection = {'metadata': metadata, 'features': 'features.h5'}
    _write_collection(uid, collection)

    return collection


@dispatcher.add_method
def update_collection(uid, metadata):
    """Update metadata of collection.
    """
    collections = _load_collections()

    if uid not in list(collections.keys()):
        print('Collection not found')
        return {}

    collections[uid].update(metadata)
    _write_collections(collections)
    return collections[uid]


@dispatcher.add_method
def delete_collection(uid, delete_data=True):
    """delete a collection

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

    if uid not in list(collections.keys()):
        print('Collection not found')
        return collections

    if delete_data:
        path = collections[uid]['path']
        if os.path.exists(path):
            print('deleting all data under path:', path)
            shutil.rmtree(path)

    print('removing %s from collections' % uid)
    del collections[uid]
    _write_collections(collections)
    return collections


def _collection_features_file(collection):
    collection = _load_collections().get(collection)
    if collection is None:
        raise ValueError('Collection Not Found')

    folder = collection['folder']
    path = os.path.join(util.get_data_dir(), folder)

    return os.path.join(path, 'features.h5')


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


def _get_collection_file(uid):
    collections = _load_collections()
    if uid not in collections.keys():
        raise ValueError('Collection %s not found' % uid)

    folder = collections[uid]['folder']
    path = os.path.join(util.get_data_dir(), folder)

    return os.path.join(path, 'dsl.yml')


def _load_collection(uid):
    """load collection

    """
    path = _get_collection_file(uid)

    if not os.path.exists(path):
        return {}
    
    with open(path) as f:
        return yaml.safe_load(f)


def _load_collections():
    """load list of collections

    """
    path = util.get_collections_index()

    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return yaml.safe_load(f)


def _write_collection(uid, collection):
    """write collection

    """
    with open(_get_collection_file(uid), 'w') as f:
        yaml.safe_dump(collection, f, default_flow_style=False)


def _write_collections(collections):
    """write list of collections to  file 
    """
    path = util.get_collections_index()
    with open(path, 'w') as f:
        yaml.safe_dump(collections, f, default_flow_style=False)
