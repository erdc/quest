import os

import pandas as pd

from .providers import get_services
from ..util import parse_service_uri, get_cache_dir
from ..plugins import load_providers


def get_mapped_parameters():
    """Get list of common parameters.

    Returns:
     parameters (list):
           list of common parameters

    """
    services = get_services(expand=True)
    parameters = []
    for service in services.values():
        parameters += service['parameters']
    return sorted(list(set(parameters)))


def get_parameters(service_uri, update_cache=False):
    """Get available parameters, even unmapped ones, for specified service.

    Args:
        service_uri (string, Required):
            uri of service to get parameters for
        update_cache (bool, Optional, Default=True):
            if True, update metadata cache

    Returns:
        parameters (list):
            all available parameters for specified service


    """
    provider, service, catalog_id = parse_service_uri(service_uri)
    parameters = _read_cached_parameters(provider, service, update_cache=update_cache)

    if isinstance(parameters, pd.DataFrame) and catalog_id:
        idx = parameters['service_id'] == catalog_id
        parameters = parameters[idx]

    return parameters


def new_parameter(uri, parameter_name):
    """Add new parameter to collection."""
    pass


def update_parameter():
    """Add update parameter metadata in a collection."""
    pass


def delete_parameter():
    """delete a parameter in a collection."""
    pass


def _read_cached_parameters(provider, service, update_cache=False):
    """read cached parameters."""
    cache_file = os.path.join(get_cache_dir(), provider, service + '_parameters.h5')
    if update_cache:
        return _get_parameters(provider, service, cache_file)

    try:
        parameters = pd.read_hdf(cache_file, 'table')
    except:
        parameters = _get_parameters(provider, service, cache_file)

    return parameters


def _get_parameters(provider, service, cache_file):
    driver = load_providers()[provider]
    parameters = driver.get_parameters(service)
    os.makedirs(os.path.split(cache_file)[0], exist_ok=True)
    if isinstance(parameters, pd.DataFrame):
        parameters.to_hdf(cache_file, 'table')

    return parameters
