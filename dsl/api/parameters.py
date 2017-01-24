"""API functions related to Parameters."""
from jsonrpc import dispatcher
import pandas as pd
from .services import get_services
import os
from .. import util


@dispatcher.add_method
def get_mapped_parameters():
    """Get list of  common parameters

    Returns:
     parameters (list):
           list of common parameters

    """
    services = get_services(expand=True)
    parameters = []
    for service in services.values():
        parameters += service['parameters']
    return sorted(list(set(parameters)))


@dispatcher.add_method
def get_parameters(service_uri, update_cache=False):
    """Get available parameters, even unmapped ones, for specified service

    Args:
        service_uri (string, Required):
            uri of service to get parameters for
        update_cache (bool, Optional, Default=True):
            if True, update metadata cache

    Returns:
        parameters (list):
            all available parameters for specified service


    """
    provider, service, feature = util.parse_service_uri(service_uri)
    parameters = _read_cached_parameters(provider, service,
                                         update_cache=update_cache)


    if isinstance(parameters,pd.DataFrame) and feature:
        idx = parameters['service_id'] == feature
        parameters = parameters[idx]

    return parameters


@dispatcher.add_method
def new_parameter(uri, parameter_name, ):
    """Add new parameter to collection."""
    pass


@dispatcher.add_method
def update_parameter():
    """Add update parameter metadata in a collection."""
    pass


@dispatcher.add_method
def delete_parameter():
    """delete a parameter in a collection."""
    pass


def _read_cached_parameters(provider, service, update_cache=False):
    """read cached features."""
    cache_file = os.path.join(util.get_cache_dir(), provider, service+'_parameters.h5')
    if update_cache:
        return _get_parameters(provider, service, cache_file)

    try:
        parameters = pd.read_hdf(cache_file, 'table')
    except:
        parameters = _get_parameters(provider, service, cache_file)

    return parameters


def _get_parameters(provider, service, cache_file):
    driver = util.load_services()[provider]
    parameters = driver.get_parameters(service)
    util.mkdir_if_doesnt_exist(os.path.split(cache_file)[0])
    if isinstance(parameters, pd.DataFrame):
        parameters.to_hdf(cache_file, 'table')

    return parameters
