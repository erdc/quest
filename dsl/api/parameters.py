from jsonrpc import dispatcher
import pandas as pd
from .services import get_services
import os
from .. import util

@dispatcher.add_method
def get_common_parameters():
    """get list common parameters

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
    uri = util.parse_uri(uri)
    if uri['resource']=='webservice':
        parameters = _read_cached_parameters(uri['name'], uri['service'], update_cache=update_cache)

    if uri['resource']=='collection':
        raise NotImplementedError

    return parameters    


def new_parameter():
    pass


def update_parameters():
    pass

   
def delete_parameters():
    pass
   

def _read_cached_parameters(provider, service, update_cache=False):
    """read cached features
    """
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