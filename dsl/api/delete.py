"""API functions related to deleting resources.

delete fn for collections/features/datasets
"""

from jsonrpc import dispatcher
import pandas as pd
import os
import shutil

# from .projects import active_db
from .features import get_features
from .datasets import get_datasets
from .. import util
from .database import get_db, db_session
from .projects import _get_project_dir
# from . import db


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

    db = get_db()
    for uri in uris:
        if resource == 'collections':
            # delete all datasets and all features and folder
            features = get_features(collections=uri)
            delete(features)
            with db_session:
                db.Collection[uri].delete()

            path = _get_project_dir()
            path = os.path.join(path, uri)
            if os.path.exists(path):
                print('deleting all data under path: %s' % path)
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
