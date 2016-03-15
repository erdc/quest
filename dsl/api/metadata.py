"""API functions related to metadata.

get/update metadata for projects/collections/datasets
"""

from jsonrpc import dispatcher
import pandas as pd

from .projects import active_db
from .. import util
from . import db


@dispatcher.add_method
def get_metadata(uris, as_dataframe=False):
    """Get metadata for uris.

    Args:
        uris (string, comma separated string, list of strings):
            list of uris to retrieve metadata for.

    Returns:
        metadata (dict or pd.DataFrame): metadata at each uri keyed on uris
    """
    uris = util.listify(uris)

    df = pd.DataFrame(uris, columns=['uri'])
    df['type'] = 'collection'

    uuid_idx = df['uri'].apply(util.is_uuid)
    service_idx = df['uri'].str.startswith('svc://')
    feature_idx = uuid_idx & df['uri'].str.startswith('f')
    dataset_idx = uuid_idx & df['uri'].str.startswith('d')

    df['type'][service_idx] = 'service'
    df['type'][feature_idx] = 'feature'
    df['type'][dataset_idx] = 'dataset'
    df.set_index('uri', drop=False, inplace=True)

    # group dataframe by type
    grouped = df.groupby('type')

    metadata = []

    # get metadata for service type uris
    if 'service' in grouped.groups.keys():
        svc_df = grouped.get_group('service')
        svc_df = pd.DataFrame(svc_df['uri'].apply(util.parse_service_uri).tolist(),
                              columns=['provider', 'service', 'feature'])

        for (provider,service), grp in svc_df.groupby(['provider', 'service']):
            driver = util.load_drivers('services', names=provider)[provider].driver
            features = driver.get_features(service)
            selected_features = grp['feature'].tolist()
            if None not in selected_features:
                features = features.ix[selected_features]

        metadata.append(features)

    if 'collection' in grouped.groups.keys():
        # get metadata for collections
        tmp_df = grouped.get_group('collection')
        collections = db.read_all(active_db(), 'collections', as_dataframe=True)
        collections = collections.ix[tmp_df['uri'].tolist()]
        metadata.append(collections)

    if 'feature' in grouped.groups.keys():
        # get metadata for features
        tmp_df = grouped.get_group('feature')
        features = db.read_all(active_db(), 'features', as_dataframe=True)
        features = features.ix[tmp_df['uri'].tolist()]
        metadata.append(features)

    if 'dataset' in grouped.groups.keys():
        # get metadata for datasets
        tmp_df = grouped.get_group('dataset')
        datasets = db.read_all(active_db(), 'datasets', as_dataframe=True)
        datasets = datasets.ix[tmp_df['uri'].tolist()]
        metadata.append(datasets)

    metadata = pd.concat(metadata)

    if not as_dataframe:
        metadata = metadata.to_dict()

    return metadata
