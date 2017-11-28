"""API functions related to metadata.

get/update metadata for projects/collections/datasets.
"""

from jsonrpc import dispatcher
import pandas as pd
import geopandas as gpd
import shapely.wkt

from .. import util
from .database import get_db, db_session, select_collections, select_features, select_datasets


@dispatcher.add_method
def get_metadata(uris, as_dataframe=False):
    """Get metadata for uris.

    Args:
        uris (string, comma separated string, or list of strings, Required):
            list of uris to retrieve metadata for
        as_dataframe (bool, Optional, Default=False):
           include details of newly created dataset as a pandas Dataframe

    Returns:
        metadata (dict or pd.DataFrame, Default=dict):
            metadata at each uri keyed on uris
    """
    # group uris by type
    grouped_uris = util.classify_uris(uris)

    # handle case when no uris are passed in
    if not any(grouped_uris):
        metadata = pd.DataFrame()
        if not as_dataframe:
            metadata = metadata.to_dict(orient='index')
        return metadata

    metadata = []

    # get metadata for service type uris
    if 'services' in grouped_uris.groups.keys():
        svc_df = grouped_uris.get_group('services')
        svc_df[['provider', 'service', 'feature']] = svc_df['uri'].apply(util.parse_service_uri).apply(pd.Series)

        for (provider, service), grp in svc_df.groupby(['provider', 'service']):
            # svc = .format(provider, service)
            driver = util.load_providers()[provider]
            features = driver.get_features(service)
            selected_features = grp['uri'].tolist()
            if None not in selected_features:
                features = features.loc[selected_features]

            metadata.append(features)

    if 'collections' in grouped_uris.groups.keys():
        # get metadata for collections
        tmp_df = grouped_uris.get_group('collections')
        collections = select_collections(lambda c: c.name in tmp_df['uri'].tolist())
        collections = pd.DataFrame(collections)
        collections.set_index('name', inplace=True, drop=False)

        metadata.append(collections)

    if 'features' in grouped_uris.groups.keys():
        # get metadata for features
        tmp_df = grouped_uris.get_group('features')
        features = select_features(lambda c: c.name in tmp_df['uri'].tolist())
        features = gpd.GeoDataFrame(features)
        if not features.empty:
            features['geometry'] = features['geometry'].apply(
                                        lambda x: shapely.wkt.loads(x))
            features.set_geometry('geometry')
            features.index = features['name']
        metadata.append(features)

    if 'datasets' in grouped_uris.groups.keys():
        # get metadata for datasets
        tmp_df = grouped_uris.get_group('datasets')
        datasets = select_datasets(lambda c: c.name in tmp_df['uri'].tolist())
        datasets = pd.DataFrame(datasets)
        datasets.set_index('name', inplace=True, drop=False)

        metadata.append(datasets)

    metadata = pd.concat(metadata)

    if not as_dataframe:
        metadata = metadata.to_dict(orient='index')

    return metadata


@dispatcher.add_method
def update_metadata(uris, display_name=None, description=None,
                    metadata=None, quest_metadata=None):
    """Update metadata for resource(s)

    Args:
        uris (string, comma separated string, or list of strings, Required):
            list of uris to update metadata for.
        display_name (string or list, Optional,Default=None):
            display name for each uri
        description (string or list, Optional,Default=None):
            description for each uri
        metadata (dict or list of dicts, Optional, Default=None):
            user defiend metadata
        quest_metadata (dict or list of dicts, Optional, Default=None):
            metadata used by QUEST
    Returns:
        metadata (dict):
            metadata at each uri keyed on uris
    """
    # group uris by type
    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=['services'], require_same_type=True)
    resource = list(grouped_uris)[0]
    uris = grouped_uris[resource]

    n = len(uris)
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

        if not isinstance(quest_metadata, list):
                    quest_metadata = [quest_metadata] * n
    else:
        display_name = [display_name]
        description = [description]
        metadata = [metadata]
        quest_metadata = [quest_metadata]

    for uri, name, desc, meta, quest_meta in zip(uris, display_name,
                                               description, metadata,
                                               quest_metadata):
        if quest_meta is None:
            quest_meta = {}

        if name:
            quest_meta.update({'display_name': name})
        if desc:
            quest_meta.update({'description': desc})
        if meta:
            quest_meta.update({'metadata': meta})

        db = get_db()
        with db_session:
            if resource == 'collections':
                entity = db.Collection[uri]
            elif resource == 'features':
                entity = db.Feature[uri]
            elif resource == 'datasets':
                entity = db.Dataset[uri]

            entity.set(**quest_meta)

    return get_metadata(uris)
