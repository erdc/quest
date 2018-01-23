"""API functions related to Services.

Providers are inferred by aggregating information from service plugins.
"""
from __future__ import absolute_import
from __future__ import print_function
from jsonrpc import dispatcher
from .. import util
import os
import requests


@dispatcher.add_method
def get_providers(expand=None):
    """Return list of Providers.

    Args:
         expand (bool, Optional, Default=None):
            include providers' details and format as dict
    Returns:
        providers (list or dict,Default=list):
            list of all available providers

    """
    providers = util.load_providers() #util.load_drivers('services')
    p = {k: v.metadata for k, v in providers.items()}
    if not expand:
        p = sorted(p.keys())

    return p


@dispatcher.add_method
def get_services(expand=None, parameter=None, service_type=None):
    """Return list of Services.

    Args:
         expand (bool, Optional, Default=False):
            include services' details and format as dict
         parameter (string, Optional, Default=None):
         service_type (string, Optional, Default=None'):
            filter to only include specific type

    Returns:
          services (list or dict, Default=dict):
            all available services

    """
    providers = util.load_providers() # util.load_drivers('services')
    services = {}
    for provider, svc in providers.items():
        for service, svc_metadata in svc.get_services().items():
            name = 'svc://%s:%s' % (provider, service)
            if service_type == svc_metadata['service_type'] or service_type is None:
                if parameter in svc_metadata['parameters'] or parameter is None:
                    svc_metadata.update({'name': name})
                    services[name] = svc_metadata

    if not expand:
        services = sorted(services.keys())

    return services


@dispatcher.add_method
def add_provider(uri):
    """Add a custom web service created from a file or http folder.

    Converts a local/network or http folder that contains a quest.yml
    and associated data into a service that can be accessed through quest


    Args:
        uri (string, Required):
            uri of new 'user' service
    Returns:
        message (string):
            status of adding service (i.e. failed/success)
    """
    valid = False
    if uri.startswith('http'):
        url = uri.rstrip('/') + '/quest.yml'
        r = requests.head(url, verify=False)
        if (r.status_code == requests.codes.ok):
            valid = True
    else:
        path = os.path.join(uri, 'quest.yml')
        valid = os.path.isfile(path)

    if valid:
        user_services = util.get_settings()['USER_SERVICES']
        if uri not in user_services:
            user_services.append(uri)
            util.update_settings({'USER_SERVICES': user_services})
            util.save_settings()
            msg = 'service added'
        else:
            msg = 'service already present'
    else:
        msg = 'service does not have a quest config file (quest.yml)'

    return msg


@dispatcher.add_method
def delete_provider(uri):
    """Remove 'user' service.

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:
        message (string):
            status of deleting service

    """
    if uri.startswith('svc://'):
        provider, service, _ = util.parse_service_uri(uri)
        if not provider.startswith('user'):
            raise ValueError('Can only remove user services')

        uri = get_providers(expand=True)[provider].get('service_uri')

    user_services = util.get_settings()['USER_SERVICES']
    if uri in user_services:
        user_services.remove(uri)
        util.update_settings({'USER_SERVICES': user_services})
        util.save_settings()
        msg = 'service removed'
    else:
        msg = 'service not found'

    return msg


@dispatcher.add_method
def authenticate_provider(uri):
    """Authenticate the user.

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:


    """
    # driver = util.load_providers()[uri]
    # driver.authenticate_me()














