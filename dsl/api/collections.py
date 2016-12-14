"""API functions related to Collections."""
from __future__ import print_function
from jsonrpc import dispatcher
from .. import util
from .projects import get_active_project, get_projects
import os
import pandas as pd
from .database import get_db, db_session


@dispatcher.add_method
def get_collections(expand=False, as_dataframe=False):
    """Get available collections

    Collections are folders on the local disk that contain downloaded or
    created data along with associated metadata.

    Args:
        expand (bool, optional, default=False):
            include collection details and format as dict
        as_dataframe (bool, optional, default=False):
            include collection details and format as pandas dataframe

    Returns:
        If expand/as_dataframe are True the returns available collections
        as a dict/dataframe otherwise returns list of collection names.
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

    db = get_db()
    with db_session:
        db.Collection(name=name,
                      display_name=display_name,
                      description=description,
                      metadata=metadata)

    return _load_collection(name)


def _get_project_dir():
    return get_projects(expand=True)[get_active_project()]['folder']


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
