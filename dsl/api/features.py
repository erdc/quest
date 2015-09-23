"""API functions related to Features

Features are unique identifiers with a web service or collection.
"""
from ..utils import parse_uri

def get_features(uri, filters, as_dataframe=False, as_geojson=True):
    """
    """
    uri = parse_uri(uri)

    if uri['resource']=='webservice':
        service = _load_services()[name]
        features = service.get_features(uri['name'], filters=filters)

    if uri['resource']=='collection':
        raise NotImplementedError

    if as_geojson and as_dataframe:
        error_msg = 'Must specify only as_dataframe or as_geojson not both'
        raise ValueError(error_msg)

    if as_dataframe:
        return 

def new_feature():
    pass

    
def update_feature():
    pass

    
def delete_feature():
    pass

    
def _read_cached_features(uri):
    """read cached features
    """
    pass


def _write_cached_features(uri):
    pass