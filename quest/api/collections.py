import os

import pandas as pd

from .projects import _get_project_dir
from ..database.database import get_db, db_session


def get_collections(expand=False, as_dataframe=False):
    """Get available collections.

    Collections are folders on the local disk that contain downloaded or
    created data along with associated metadata.

    Args:
        expand (bool, Optional, Default=False):
            include collection details and format as dict
        as_dataframe (bool, Optional, Default=False):
            include collection details and format as pandas dataframe

    Returns:
        collections (list, dict, or pandas dataframe, Default=list):
            all available collections

    """

    collections = _load_collections()
    if not expand and not as_dataframe:
        collections = list(collections.keys())

    if as_dataframe:
        collections = pd.DataFrame.from_dict(collections, orient='index')

    return collections


def new_collection(name, display_name=None, description=None, metadata=None):
    """Create a new collection.

    Create a new collection by creating a new folder in project directory
    and adding collection metadata in project database.

    Args:
        name (string, Required):
            Name of the collection used in all quest function calls,must be unique. Will also be the folder name of the collection
        display_name (string, Optional, Default=None):
            display name for collection
        description (string, Optional, Default=None):
            description of collection
        metadata (dict, Optional, Default=None):
            user defined metadata

    Returns:
        collection (dict)
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
    os.makedirs(path, exist_ok=True)

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
