"""API functions related to Collections."""
from __future__ import print_function
import os
from jsonrpc import dispatcher
from .. import util
from .projects import _get_project_dir
import pandas as pd
from .database import get_db, db_session
import os


@dispatcher.add_method
def get_collections(expand=False, as_dataframe=False):
    """Get available collections

    Collections are folders on the local disk that contain downloaded or
    created data along with associated metadata.

    Args:
        expand (bool, Optional, Default=False):
            include collection details and format as dict
        as_dataframe (bool, Optional, Default=False):
            include collection details and format as pandas dataframe

    Returns:
        collections (list, dict, or pandas Dataframe, Default=list):
            list of collections if expand/as_dataframe are False

    """

    collections = _load_collections()
    if not expand and not as_dataframe:
        collections = list(collections.keys())

    if as_dataframe:
        collections = pd.DataFrame.from_dict(collections, orient='index')

    return collections


@dispatcher.add_method
def new_collection(name, display_name=None, description=None, metadata=None):
    """Create a new collection.

    Create a new collection by creating a new folder in project directory
    and adding collection metadata in project database.

    Args:
        name (string, Required):
            Name of the collection used in all dsl function calls,must be unique. Will also be the folder name of the collection
        display_name (string, Optional, Default=None):
            display name for collection
        description (string, Optional, Default=None):
            description of collection
        metadata (dict, Optional, Default=None):
            user defined metadata

    Returns:
        collection_details (dict)
            details of the newly created collection
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

    db = get_db()
    with db_session:
        db.Collection(name=name,
                      display_name=display_name,
                      description=description,
                      metadata=metadata)

    return _load_collection(name)


def _load_collection(name):
    """load collection."""
    db = get_db()
    with db_session:
        return db.Collection.select(lambda c: c.name == name).first().to_dict()


def _load_collections():
    """load list of collections."""
    db = get_db()
    with db_session:
        return {c.name: c.to_dict() for c in db.Collection.select(lambda c: c)}
