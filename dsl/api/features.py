"""API functions related to Features

Features are unique identifiers with a web service or collection.
"""
from jsonrpc import dispatcher
import os
import pandas as pd
from .. import util
from .services import get_services


@dispatcher.add_method
def get_features(uris, geom_type=None, parameter=None, bbox=None, as_dataframe=False, update_cache=False):
    """
    """
    uris = util.listify(uris)
    features = []
    for uri in uris:
        uri = util.parse_uri(uri)
        if uri['service'] is None:
            svc = util.load_service(uri)
            services = svc.get_services()
        else:
            services = [uri['service']]

        for service in services:
            if uri['resource']=='webservice':
                features.append(_get_features(uri['name'], service, update_cache=update_cache))

            if uri['resource']=='collection':
                raise NotImplementedError

    features = pd.concat(features)

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


    features['uri'] = features.index 
    if not as_dataframe:
        features = util.to_geojson(features)

    return features


def new_feature():
    """return new feature id
    """
    pass

    
def update_feature():
    """return 
    """
    pass

    
def delete_feature():
    pass


def search_features(filters=None):
    pass


def _get_features(provider, service, update_cache):
    driver = util.load_drivers('services', names=provider)[provider].driver
    features = driver.get_features(service, update_cache=update_cache)
    features.index = features.index.map(lambda x: 'webservice://%s::%s::%s' % (provider,service,x))

    return features