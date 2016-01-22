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
    services = get_services()
    parameters = []
    for service in services.values():
        parameters += service['parameters']
    return list(set(parameters))


@dispatcher.add_method
def get_parameters(uri, update_cache=False):
    """get list of all parameters available, even unmapped ones."""
    uri = util.parse_uri(uri)
    if uri['resource'] == 'service':
        parameters = _read_cached_parameters(uri['uid'], uri['service'],
                                             update_cache=update_cache)
        if uri['feature']:
            idx = parameters['feature_id'] == uri['feature']
            parameters = parameters[idx]

    if uri['resource'] == 'collection':
        raise NotImplementedError

    return parameters


def new_parameter(uri, parameter_name, ):
    """Add new parameter to collection."""
    pass


def update_parameter():
    """Add update parameter metadata in a collection."""
    pass


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
    parameters.to_hdf(cache_file, 'table')

    return parameters
