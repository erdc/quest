"""API functions related to Features

Features are unique identifiers with a web service or collection.
"""
from ..util import parse_uri
import pandas as pd


def get_features(uri, filters, as_dataframe=False):
    """
    """
    uri = parse_uri(uri)

    if uri['resource']=='webservice':
        service = _load_services()[name]
        features = service.get_features(uri['name'], filters=filters)

    if uri['resource']=='collection':
        raise NotImplementedError

    if isinstance(features, dict):
        if features.get('type')!='FeatureCollection'
            features = _to_geojson(features)

    if as_dataframe:
        

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

    
def _read_cached_features(uri):
    """read cached features
    """
    pass


def _write_cached_features(uri):
    pass