"""API functions related to Features.

Features are unique identifiers with a web service or collection.
"""
from jsonrpc import dispatcher
import pandas as pd
from .. import util
from .collections import (
        _read_collection_features,
        _write_collection_features,
    )


@dispatcher.add_method
def add_features_to_collection(collection, uris, geom_type=None,
                               parameter=None, parameter_code=None, bbox=None,
                               filters=None, update_cache=False):
    """Add features to a collection based on the passed in uris.

    This does not download datasets, it just adds features and parameters
    to a collection.

    When the features are added into a collection they are given a new uid.
    The original uid is saved as 'external_uri'. If external_uri already exists
    (i.e. Feature was originally from usgs-nwis but is being copied from one
    collection to another) then does not overwrite external_uri.

    If a features with matching external_uri are merged and the parameter list
    updated. todo: FEATURE NOT IMPLEMENTED, Currently, new features will be
    created.

    Args:
        collection (string): uid of collection
        uris (string, comma separated strings, list of strings): list of uris
            to search in for features. If uri specifies a parameter and
            parameter arg is None then use set the parameter to the uri value
        geom_type (string, optional): filter features by geom_type, i.e.
            point/line/polygon
        parameter (string, optional): filter features by parameter
        parameter_code (string, optional): filter features by parameter_code
        bbox (string, optional): filter features by bounding box
        filters (dict, optional): filter features by key/value pairs. The
            provided keys are the metadata field names and the values are the
            filters.
        as_cache (bool, optional): Defaults to False, if True, update metadata
            cache

    Returns:
        True on success.
    """
    new_features = get_features(uris, geom_type=geom_type, parameter=parameter,
                                parameter_code=parameter_code, bbox=bbox,
                                filters=filters, update_cache=update_cache,
                                as_dataframe=True)

    # if external_uri already exists don't overwrite
    # this preserves external metadata when copying features
    # from one collection to another
    if 'external_uri' not in new_features.columns:
        new_features['external_uri'] = new_features.index
        new_features['external_id'] = new_features['feature_id']
        new_features['external_parameters'] = new_features['parameters']
        new_features['external_parameter_codes'] = new_features['parameter_codes']
        del new_features['parameters']
        del new_features['parameter_codes']

    # assign new feature ids
    new_features['feature_id'] = [util.uid() for i in range(len(new_features))]

    existing = _read_collection_features(collection)
    if not existing.empty:
        new_features = pd.concat([existing, new_features])
        new_features = new_features.drop_duplicates(subset='external_uri')

    new_features = new_features.set_index('feature_id', drop=False)
    new_features.index = new_features.index.map(
                            lambda x: 'collection://%s::%s' % (collection, x))
    _write_collection_features(collection, new_features)

    if parameter:
        # col =_load_collection(collection)
        # p = col.get('parameters')
        # ****todo****
        # WRITE NEW PARAMETER TO PARAMETER YML FILE
        # LOOK AT parameters.yml file in test directory
        pass

    return True


@dispatcher.add_method
def get_features(uris, geom_type=None, parameter=None, parameter_code=None,
                 bbox=None, filters=None, as_dataframe=False,
                 update_cache=False):
    """Retrieve list of features from resources.

    currently ignores parameter and dataset portion of uri
    if uris contain feature, then return exact feature.

    Args:
        uris (string, comma separated strings, list of strings): list of uris
            to search in for features. If uri specifies a parameter and
            parameter arg is None then use set the parameter to the uri value
        geom_type (string, optional): filter features by geom_type, i.e.
            point/line/polygon
        parameter (string, optional): filter features by parameter
        parameter_code (string, optional): filter features by parameter code
        bbox (string, optional): filter features by bounding box
        filters (dict, optional): filter features by key/value pairs. The
            provided keys are the metadata field names and the values are the
            filters.
        as_dataframe (bool, optional): Defaults to False, return features as
            a pandas DataFrame indexed by feature uris instead of geojson
        as_cache (bool, optional): Defaults to False, if True, update metadata
            cache.

    Returns:
        features (dict|pandas.DataFrame): geojson style dict (default) or
            pandas.DataFrame

    """
    uris = util.listify(uris)
    features = []
    for uri in uris:
        uri = util.parse_uri(uri)
        if uri['uid'] is None:
            raise ValueError('Service/Collection uid must be specified')

        if uri['parameter'] and parameter is None:
            parameter = uri['parameter']

        if uri['resource'] == 'service':
            if uri['service'] is None:
                svc = util.load_service(uri)
                services = svc.get_services()
            else:
                services = [uri['service']]

            for service in services:
                # seamless not implemented yet
                tmp_feats = _get_features(uri['uid'], service,
                                          update_cache=update_cache)
                if uri['feature'] is not None:
                    tmp_feats = tmp_feats[
                                    tmp_feats['feature_id'] == uri['feature']
                                ]
                features.append(tmp_feats)

        if uri['resource'] == 'collection':
            tmp_feats = _read_collection_features(uri['uid'])
            if uri['feature'] is not None:
                tmp_feats = tmp_feats[
                                tmp_feats['feature_id'] == uri['feature']
                            ]
            features.append(tmp_feats)

    features = pd.concat(features)

    if filters:
        for k, v in filters.items():
            idx = features[k] == v
            features = features[idx]

    if bbox:
        xmin, ymin, xmax, ymax = [float(x) for x in util.listify(bbox)]
        idx = (features.longitude > xmin) \
            & (features.longitude < xmax) \
            & (features.latitude > ymin) \
            & (features.latitude < ymax)
        features = features[idx]

    if geom_type:
        idx = features.geom_type.str.lower() == geom_type.lower()
        features = features[idx]

    if parameter:
        idx = features.parameters.str.contains(parameter)
        features = features[idx]

    if parameter_code:
        idx = features.parameters.str.contains(parameter)
        features = features[idx]

    # remove duplicate indices
    features.reset_index().drop_duplicates(subset='index').set_index('index')

    if not as_dataframe:
        features = util.to_geojson(features)

    return features


@dispatcher.add_method
def new_feature(uri, geom_type, geom_coords, metadata={}):
    """Add a new feature to a collection.

    (ignore feature/parameter/dataset in uri)

    Args:
        uri (string): uri of collection
        geom_type (string, optional): point/line/polygon
        geom_coords (string, optional): geometric coordinates
        metadata (dict, optional): metadata at the new feature

    Returns
    -------
        feature_id : str
            uri of newly created feature

    """
    uri = util.parse_uri(uri)
    if uri['resource'] != 'collection':
        raise NotImplementedError

    collection = uri['uid']
    metadata.update({'geom_type': geom_type, 'geom_coords': geom_coords})
    metadata.update({})
    uid = 'collection://' + collection + '::' + util.uid()

    feature = pd.Series(metadata, name=uid)
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

        collection = uri['uid']
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

    collection = uri['uid']
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
    features.index = features.index.map(
                            lambda x: 'service://%s::%s::%s'
                            % (provider, service, x))

    return features
