"""API functions related to Features

Features are unique identifiers with a web service or collection.
"""
from jsonrpc import dispatcher
import os
import pandas as pd
from .. import util
from .services import get_services
from .collections import _read_collection_features, _write_collection_features


@dispatcher.add_method
def add_to_collection(collection, uris):
    """Add uris to collection
    todo NEEDS WORK
    """
    uris = util.listify(uris)
    new_features = get_features(uris, as_dataframe=True)
    existing = _read_collection_features(collection)
    df = pd.concat([existing, new_features])
    df = df.reset_index().drop_duplicates(subset='index').set_index('index')
    _write_collection_features(collection, df)
    
    return


@dispatcher.add_method
def get_features(uris, geom_type=None, parameter=None, bbox=None, tags=None, as_dataframe=False, update_cache=False):
    """Retrieve list of features from a uri.

    currently ignores parameter and dataset portion of uri
    if uris contain feature, then return exact feature.

    Parameters
    ----------
        uris: str, comma separated str, list of str
            list of uris to search in for features
        geom_type: str
            filter results by geom_type - point/line/polygon
        parameter: str
            filter results by parameter
        bbox: str
            filter results by bounding box
        tags: dict
            filter results by key/value pairs. NOTIMPLEMENTED
        as_dataframe: bool
            If True, return features as pandas DataFrame, else
            return a geojson style dict
    Returns
    -------
        features: geojson style dict or pandas.DataFrame

    """
    uris = util.listify(uris)
    features = []
    for uri in uris:
        uri = util.parse_uri(uri)
        if uri['uid'] is None:
            raise ValueError('Webservice/Collection uid must be specified')

        if uri['resource']=='webservice':
            if uri['service'] is None:
                svc = util.load_service(uri)
                services = svc.get_services()
            else:
                services = [uri['service']]

            for service in services:
                # seamless not implemented yet
                tmp_feats = _get_features(uri['uid'], service, update_cache=update_cache)
                if uri['feature'] is not None:
                    tmp_feats = tmp_feats[tmp_feats['external_feature_id']==uri['feature']]
                features.append(tmp_feats)

        if uri['resource']=='collection':
            tmp_feats = _read_collection_features(uri['uid'])
            if uri['feature'] is not None:
                tmp_feats = tmp_feats[tmp_feats['external_feature_id']==uri['feature']]
            features.append(tmp_feats)

    features = pd.concat(features)

    if tags:
        NotImplementedError('Tag search not implemented')

    if bbox:
        xmin, ymin, xmax, ymax = [float(x) for x in util.listify(bbox)]
        idx = (features.longitude > xmin) & (features.longitude < xmax) & (features.latitude > ymin) & (features.latitude < ymax)
        features = features[idx]

    if geom_type:
        idx = features.geom_type.str.lower() == geom_type.lower()
        features = features[idx]

    if parameter:
        idx = features.parameters.str.contains(parameter)
        features = features[idx]
        features.index = features.index.map(lambda x: '%s::%s' % (x, parameter))

    #remove duplicate indices
    features.reset_index().drop_duplicates(subset='index').set_index('index')
    features['external_uri'] = features.index
    if not as_dataframe:
        features = util.to_geojson(features)

    return features


def new_feature(uri, geom_type, geom_coords, metadata={}):
    """Add a new feature to a collection 
    ignore feature/parameter/dataset in uri

    NOT FULLY IMPLEMENTED

    Returns
    -------
        feature_id : str
            uid of newly created feature
    
    """
    uri = util.parse_uri(uri)
    if uri['resource']!='collection':
        raise NotImplementedError
    
    feature = {
        util.uid()
    }
    return feature
    

    
def update_feature(uri, metadata={}):
    """Change metadata and properties of feature to a uri (probably only collection) 
    """
    pass

    
def delete_feature(uri):
    """Remove feature/metadata from a collection?
    """
    pass


def search_features(filters=None):
    """SOme sort of free form search through features. NOTIMPLEMENTED.
    """
    pass


def _get_features(provider, service, update_cache):
    driver = util.load_drivers('services', names=provider)[provider].driver
    features = driver.get_features(service, update_cache=update_cache)
    features.index = features.index.map(lambda x: 'webservice://%s::%s::%s' % (provider,service,x))

    return features