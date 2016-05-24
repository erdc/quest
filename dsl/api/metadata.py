"""API functions related to metadata.

get/update metadata for projects/collections/datasets.
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
    # group uris by type
    df = util.classify_uris(uris)
    grouped = df.groupby('type')

    metadata = []
    # get metadata for service type uris
    if 'services' in grouped.groups.keys():
        svc_df = grouped.get_group('services')
        svc_df = pd.DataFrame(svc_df['uri'].apply(util.parse_service_uri).tolist(),
                              columns=['provider', 'service', 'feature'])

        for (provider,service), grp in svc_df.groupby(['provider', 'service']):
            driver = util.load_drivers('services', names=provider)[provider].driver
            features = driver.get_features(service)
            selected_features = grp['feature'].tolist()
            if None not in selected_features:
                features = features.ix[selected_features]

            features['_service'] = 'svc://{}:{}'.format(provider, service)
            features.index = features['_service'] + '/' + features['_service_id']
            features['_name'] = features.index
            metadata.append(features)

    if 'collections' in grouped.groups.keys():
        # get metadata for collections
        tmp_df = grouped.get_group('collections')
        collections = db.read_all(active_db(), 'collections', as_dataframe=True)
        collections = collections.ix[tmp_df['uri'].tolist()]
        metadata.append(collections)

    if 'features' in grouped.groups.keys():
        # get metadata for features
        tmp_df = grouped.get_group('features')
        features = db.read_all(active_db(), 'features', as_dataframe=True)
        features = features.ix[tmp_df['uri'].tolist()]
        metadata.append(features)

    if 'datasets' in grouped.groups.keys():
        # get metadata for datasets
        tmp_df = grouped.get_group('datasets')
        datasets = db.read_all(active_db(), 'datasets', as_dataframe=True)
        datasets = datasets.ix[tmp_df['uri'].tolist()]
        metadata.append(datasets)

    metadata = pd.concat(metadata)

    if not as_dataframe:
        metadata = metadata.to_dict(orient='index')

    return metadata


@dispatcher.add_method
def update_metadata(uris, display_name=None, description=None,
                    metadata=None, dsl_metadata=None):
    """Update metadata for resource(s)

    Args:
        uris (string, comma separated string, list of strings):
            list of uris to update metadata for.
        display_name (string or list, optional): display name for each uri
        description (string or list, optional): description for each uri
        metadata (dict or list of dicts): metadata to be updated

    Returns:
        metadata (dict or pd.DataFrame): metadata at each uri keyed on uris
    """
    # group uris by type
    df = util.classify_uris(uris)
    uris = util.listify(uris)
    resource = pd.unique(df['type']).tolist()

    if len(resource) > 1:
        raise ValueError('All uris must be of the same type')

    resource = resource[0]
    if resource == 'service':
        raise ValueError('Metadata for service uris cannot be updated')

    n = len(df)
    if n > 1:
        if display_name is None:
            display_name = [None] * n
        elif not isinstance(display_name, list):
            raise ValueError('display_name must be a list if more that one uri is passed in')

        if description is None:
            description = [None] * n
        elif not isinstance(description, list):
            raise ValueError('description must be a list if more that one uri is passed in')

        if not isinstance(metadata, list):
            metadata = [metadata] * n

        if not isinstance(dsl_metadata, list):
                    dsl_metadata = [dsl_metadata] * n
    else:
        display_name = [display_name]
        description = [description]
        metadata = [metadata]
        dsl_metadata = [dsl_metadata]

    for uri, name, desc, metadata, dsl_metadata in zip(uris, display_name,
                                                       description, metadata,
                                                       dsl_metadata):
        if dsl_metadata is None:
            dsl_metadata = {}

        if name:
            dsl_metadata.update({'display_name': display_name})
        if desc:
            dsl_metadata.update({'description': description})

        db.upsert(active_db(), resource, uri,
                  dsl_metadata=dsl_metadata,
                  metadata=metadata)

    return get_metadata(uris)
