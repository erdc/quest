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
    )


@dispatcher.add_method
def add_features(collection, features):
    """Add features to a collection based on the passed in uris.

    This does not download datasets, it just adds features to a collection.

    When the features are added into a collection they are given a new name.

    TODO modify this based on new db format

    The original name is saved as 'external_uri'. If external_uri already exists
    (i.e. Feature was originally from usgs-nwis but is being copied from one
    collection to another) then does not overwrite external_uri.

    If a features with matching external_uri are merged and the parameter list
    updated. todo: FEATURE NOT IMPLEMENTED, Currently, new features will be
    created.

    Args:
        collection (string): name of collection
        features (string, comma separated strings, list of strings): list of
            feature uris to add to the collection.

    Returns:
        True on success.
    """
    if not isinstance(features, pd.DataFrame):
        features = get_features(features, as_dataframe=True)

    result = db.upsert_features(active_db(), features)

    return True


@dispatcher.add_method
def get_features(uris, as_dataframe=False, update_cache=False, filters=None):
    """Retrieve list of features from resources.

    currently ignores parameter and dataset portion of uri
    if uris contain feature, then return exact feature.

    Args:
        uris (string, comma separated strings, list of strings): list of uris
            to search in for features. If uri specifies a parameter and
            parameter arg is None then use set the parameter to the uri value
        as_dataframe (bool, optional): Defaults to False, return features as
            a pandas DataFrame indexed by feature uris instead of geojson
        as_cache (bool, optional): Defaults to False, if True, update metadata
            cache.
        filters (dict, optional): filter features
            available filters:
                geom_type (string, optional): filter features by geom_type, i.e.
                    point/line/polygon
                parameter (string, optional): filter features by parameter
                parameter_code (string, optional): filter features by parameter code
                bbox (string, optional): filter features by bounding box

    Returns:
        features (dict|pandas.DataFrame): geojson style dict (default) or
            pandas.DataFrame

    """
    uris = util.listify(uris)

    #parse uris
    df = pd.DataFrame({'uri': uris})
    df = pd.DataFrame(df.uri.str.split('://').tolist(),
                      columns=['resource', 'remainder'])
    df1 = df.remainder.str.split('/', expand=True)
    del df['remainder']
    df['name'] = df1[0]
    if len(df1.columns) > 1:
        df['features'] = df1[1]

    features = []
    for (resource, name), group in df.groupby(['resource', 'name']):
        if resource not in ['service', 'collection']:
            raise ValueError('URI must be a service or collection')

        if resource == 'service':
            provider, service = name.split(':')
            tmp_feats = _get_features(provider, service,
                                      update_cache=update_cache)

            if 'features' in group.columns:
                # filter by feature/make sure feature exists
                # this may break on empty/NaN features need to check
                f = set(group['features'])
                if None in f:
                    f = f.remove(None)

                if f is not None:
                    idx = set(tmp_feats.index)
                    idx.intersection_update(f)
                    tmp_feats = tmp_feats.ix[list(idx)]

            tmp_feats.index = tmp_feats['_service_uri_']

        if resource == 'collection':
            tmp_feats = pd.DataFrame(db.read_all(active_db(), 'features')).T
            prefix = 'collection://' + name + '/'
            tmp_feats.index =  prefix + tmp_feats['_name_']

        features.append(tmp_feats)

    features = pd.concat(features)

    if filters is not None:
        for k, v in filters.items():
            if k=='bbox':
                xmin, ymin, xmax, ymax = [float(x) for x in util.listify(v)]
                idx = (features.longitude > xmin) \
                    & (features.longitude < xmax) \
                    & (features.latitude > ymin) \
                    & (features.latitude < ymax)
                features = features[idx]

            elif k=='geom_type':
                idx = features._geom_type_.str.lower() == v.lower()
                features = features[idx]

            elif k=='parameter':
                idx = features._parameters_.str.contains(v)
                features = features[idx]

            elif k=='parameter_code':
                idx = features._parameter_codes_.str.contains(v)
                features = features[idx]

            else:
                idx = features[k] == v
                features = features[idx]

    if not as_dataframe:
        features = util.to_geojson(features)

    return features


@dispatcher.add_method
def new_feature(uri, geom_type=None, geom_coords=None, metadata={}):
    """Add a new feature to a collection.

    (ignore feature/parameter/dataset in uri)

    Args:
        uri (string): uri of collection
        geom_type (string, optional): point/line/polygon
        geom_coords (string or list, optional): geometric coordinates specified
            as valid geojson coordinates (i.e. a list of lists i.e.
            '[[-94.0, 23.2], [-94.2, 23.4] ...]'
            --------- OR ---------
            [[-94.0, 23.2], [-94.2, 23.4] ...] etc)
        metadata (dict, optional): metadata at the new feature

    Returns
    -------
        feature_id : str
            uri of newly created feature

    """
    uri = util.parse_uri(uri)
    if uri['resource'] != 'collection':
        raise NotImplementedError

    collection = uri['name']

    if geom_type is not None:
        if geom_type not in ['LineString', 'Point', 'Polygon']:
            raise ValueError(
                    'geom_type must be one of LineString, Point or Polygon'
                )

        if isinstance(geom_coords, str):
            geom_coords = json.loads(geom_coords)

    metadata.update({'geom_type': geom_type, 'geom_coords': geom_coords})
    metadata.update({})
    name = 'collection://' + collection + '::' + util.name()

    feature = pd.Series(metadata, name=name)
    existing = _read_collection_features(collection)
    updated = existing.append(feature)
    _write_collection_features(collection, updated)

    return feature.name


@dispatcher.add_method
def update_feature(uri, metadata):
    """Change metadata feature in collection.

    (ignore feature/parameter/dataset in uri)

    Args:
        uri (string): uri of collection
        metadata (dict): metadata to be updated

    Returns
    -------
        True on successful update

    """
    uri_list = util.listify(uri)

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

    (ignore parameter/dataset in uri)

        Args:
            uri (string): uri of feature inside collection

        Returns
        -------
            True on successful update
    """
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
    driver = util.load_drivers('services', names=provider)[provider].driver
    features = driver.get_features(service, update_cache=update_cache)
    features['_service_uri_'] = features.index.map(
                                    lambda feat: 'service://%s:%s/%s'
                                    % (provider, service, feat))
    return features
