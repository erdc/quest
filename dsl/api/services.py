"""API functions related to Services.

Providers are inferred by aggregating information from service plugins.
"""
from __future__ import absolute_import
from __future__ import print_function
from builtins import str
from jsonrpc import dispatcher
from .. import util

import os
import requests
from stevedore import driver


@dispatcher.add_method
def get_providers(expand=None):
    """Return list of Providers."""
    providers = util.load_services() #util.load_drivers('services')
    p = {k: v.metadata for k, v in providers.items()}
    if not expand:
        p = sorted(p.keys())

    return p


@dispatcher.add_method
def get_services(expand=None, parameter=None, service_type='geo-discrete'):
    """Return list of Services."""
    providers = util.load_services() # util.load_drivers('services')
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
    """Add a custom web service created from a file or http folder

    Converts a local/network or http folder that contains a dsl.yml
    and associated data into a service that can be accessed through dsl
    """
    valid = False
    if uri.startswith('http'):
        url = uri.rstrip('/') + '/dsl.yml'
        r = requests.head(url, verify=False)
        if (r.status_code == requests.codes.ok):
            valid = True
    else:
        path = os.path.join(uri, 'dsl.yml')
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
        msg = 'service does not have a dsl config file (dsl.yml)'

    return msg


@dispatcher.add_method
def delete_provider(uri):
    """Remove 'user' service."""
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
