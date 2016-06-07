"""API functions related to Parameters."""
from jsonrpc import dispatcher
import pandas as pd
from .services import get_services
import os
from .. import util


@dispatcher.add_method
def get_mapped_parameters():
    """get list common parameters.

    Returns
    -------
    parameters : list of str,
        list of parameters available
    """
    services = get_services(metadata=True)
    parameters = []
    for service in services.values():
        parameters += service['parameters']
    return sorted(list(set(parameters)))


@dispatcher.add_method
def get_parameters(service_uri, update_cache=False):
    """Get dataframe of available parameters.

    get list of all parameters available, even unmapped ones.
    """
    provider, service, feature = util.parse_service_uri(service_uri)
    parameters = _read_cached_parameters(provider, service,
                                         update_cache=update_cache)

    if feature:
        idx = parameters['_service_id'] == feature
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
    driver = util.load_drivers('services', names=provider)[provider].driver
    parameters = driver.get_parameters(service)
    util.mkdir_if_doesnt_exist(os.path.split(cache_file)[0])
    if isinstance(parameters, pd.DataFrame):
        parameters.to_hdf(cache_file, 'table')

    return parameters
