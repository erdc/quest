"""API functions related to Features.

Features are unique identifiers with a web service or collection.
"""
import json
from jsonrpc import dispatcher
import pandas as pd

from .. import util
from . import db
from .projects import active_db
from .collections import (
        _read_collection_features,
        _write_collection_features,
        get_collections,
    )
from .metadata import get_metadata

@dispatcher.add_method
def add_features(collection, features):
    """Add features to a collection based on the passed in feature uris.

    This does not download datasets, it just adds features to a collection.
    When the features are added into a collection they are given a new
    feature id.

    If a featuture from a service already exists then it is not re-added the
    uri of the existing feature is returned (i.e. Feature was originally from
    usgs-nwis but is being copied from one collection to another) then does
    not overwrite external_uri.

    Args:
        collection (string): name of collection
        features (string, comma separated strings,
                  list of strings, pandas DataFrame): list of
            features to add to the collection.

    Returns:
        uris (list): uri's of features
    """
    if not isinstance(features, pd.DataFrame):
        features = get_metadata(features, as_dataframe=True)

    #features[~features.index.str.startswith('svc://')]['_service'] = None
    features['_collection'] = collection
    return db.upsert_features(active_db(), features)


@dispatcher.add_method
def get_features(services=None, collections=None, features=None,
                 metadata=None, as_dataframe=False, update_cache=False,
                 filters=None):
    """Retrieve list of features from resources.

    Args:
        services (comma separated strings, list of strings): list of services
            to search in for features.
        collections (comma separated strings, list of strings): list of
            collections to search in for features.
        features (comma separated strings, list of strings): list of features
            to include in search.
        metadata (bool, optional): Defaults to False. If True return feature
            metadata
        as_dataframe (bool, optional): Defaults to False, return features as
            a pandas DataFrame indexed by feature uris instead of geojson
        as_cache (bool, optional): Defaults to False, if True, update metadata
            cache.
        filters (dict, optional): filter features
            available filters:
                geom_type (string, optional): filter features by geom_type,
                    i.e. point/line/polygon
                parameter (string, optional): filter features by parameter
                parameter_code (string, optional): filter features by
                    parameter code
                bbox (string, optional): filter features by bounding box

    Returns:
        features (dict|pandas.DataFrame): geojson style dict (default) or
            pandas.DataFrame

    """
    if services is None and collections is None and features is None:
        raise ValueError('Specify at least one service, collection or feature')

    services = util.listify(services)
    collections = util.listify(collections)
    features = util.listify(features)

    all_features = []

    # get metadata for directly specified features
    if features is not None:
        all_features.append(get_metadata(features, as_dataframe=True))

    # get metadata for features in services
    for name in services or []:
        provider, service, feature = util.parse_service_uri(name)
        tmp_feats = _get_features(provider, service, update_cache=update_cache)
        all_features.append(tmp_feats)

    # get metadata for features in collections
    for name in collections or []:
        tmp_feats = pd.DataFrame(db.read_all(active_db(), 'features')).T
        if not tmp_feats.empty:
            tmp_feats = tmp_feats[tmp_feats['_collection'] == name]
            tmp_feats.index = tmp_feats['_name']
        all_features.append(tmp_feats)

    # drop duplicates fails when some columns have nested list/tuples like
    # _geom_coords. so drop based on index
    features = pd.concat(all_features).reset_index().drop_duplicates(subset='index')
    features = features.set_index('index').sort_index()

    # apply any specified filters
    if filters is not None:
        for k, v in filters.items():
            if k == 'bbox':
                xmin, ymin, xmax, ymax = [float(x) for x in util.listify(v)]
                idx = (features._longitude > xmin) \
                    & (features._longitude < xmax) \
                    & (features._latitude > ymin) \
                    & (features._latitude < ymax)
                features = features[idx]

            elif k == 'geom_type':
                idx = features._geom_type.str.lower() == v.lower()
                features = features[idx]

            elif k == 'parameter':
                idx = features._parameters.str.contains(v)
                features = features[idx]

            elif k == 'parameter_code':
                idx = features._parameter_codes.str.contains(v)
                features = features[idx]

            else:
                idx = features[k] == v
                features = features[idx]

    if not metadata and not as_dataframe:
        return features.index.astype('unicode').tolist()

    if not as_dataframe:
        features = util.to_geojson(features)

    return features


@dispatcher.add_method
def new_feature(collection, display_name=None, geom_type=None, geom_coords=None, metadata=None):
    """Add a new feature to a collection.

    Args:
        collection (string): name of collection
        display_name (string): display name of feature
        geom_type (string, optional): point/line/polygon
        geom_coords (string or list, optional): geometric coordinates specified
            as valid geojson coordinates (i.e. a list of lists i.e.
            '[[-94.0, 23.2], [-94.2, 23.4] ...]'
            --------- OR ---------
            [[-94.0, 23.2], [-94.2, 23.4] ...] etc)
        metadata (dict, optional): optional metadata at the new feature

    Returns
    -------
        uri : str
            uri of newly created feature

    """
    if collection not in get_collections():
        raise ValueError('Collection {} not found'.format(collection))

    if geom_type is not None:
        if geom_type not in ['LineString', 'Point', 'Polygon']:
            raise ValueError(
                    'geom_type must be one of LineString, Point or Polygon'
                )

        if isinstance(geom_coords, str):
            geom_coords = json.loads(geom_coords)

    uri = util.uuid('feature')
    if display_name is None:
        display_name = uri

    dsl_metadata = {
        'display_name': display_name,
        'geom_type': geom_type,
        'geom_coords': geom_coords,
        'collection': collection,
        }

    db.upsert(active_db(), 'features', uri, dsl_metadata=dsl_metadata,
              metadata=metadata)

    return uri


@dispatcher.add_method
def update_features(feature, metadata):
    """Change metadata feature in collection.

    TODO make work with db


    (ignore feature/parameter/dataset in uri)

    Args:
        features (string, comma separated strings, list of strings): uri of
            features to update
        metadata (dict): metadata to be updated

    Returns
    -------
        True on successful update

    """
    raise NotImplementedError
    features = util.listify(features)

    for uri in uri_list:
        uri_str = uri
        uri = util.parse_uri(uri)
        if uri['resource'] != 'collection':
            raise NotImplementedError

        collection = uri['name']
        existing = _read_collection_features(collection)
        if uri_str not in existing.index:
            print('%s not found in features' % uri)
            return False

        feature = existing.ix[uri_str].to_dict()
        feature.update(metadata)
        df = pd.DataFrame({uri_str: feature}).T
        updated = pd.concat([existing.drop(uri_str), df])
        _write_collection_features(collection, updated)

        print('%s updated' % uri_str)

    return True


@dispatcher.add_method
def delete_feature(uri):
    """Delete feature from collection).

    TODO make work with db

    (ignore parameter/dataset in uri)

        Args:
            uri (string): uri of feature inside collection

        Returns
        -------
            True on successful update
    """
    raise NotImplementedError
    uri_str = uri
    uri = util.parse_uri(uri)
    if uri['resource'] != 'collection':
        raise NotImplementedError

    collection = uri['name']
    existing = _read_collection_features(collection)

    if uri_str not in existing.index:
        print('%s not found in features' % uri)
        return False

    updated = existing.drop(uri_str)
    _write_collection_features(collection, updated)

    print('%s deleted from collection' % uri_str)
    return True


def _get_features(provider, service, update_cache):
    driver = util.load_services()[provider]
    features = driver.get_features(service, update_cache=update_cache)
    features['_service'] = 'svc://{}:{}'.format(provider, service)
    features.index = features['_service'] + '/' + features['_service_id']
    features['_name'] = features.index
    return features
