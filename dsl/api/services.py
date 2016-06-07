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
def get_providers(metadata=None):
    """Return list of Providers."""
    providers = util.load_services() #util.load_drivers('services')
    p = {k: v.metadata for k, v in providers.iteritems()}
    if not metadata:
        p = sorted(p.keys())

    return p


@dispatcher.add_method
def get_services(metadata=None, parameter=None, service_type=None):
    """Return list of Services."""
    providers = util.load_services() # util.load_drivers('services')
    services = {}
    for provider, svc in providers.iteritems():
        for service, svc_metadata in svc.get_services().iteritems():
            name = 'svc://%s:%s' % (provider, service)
            if service_type == svc_metadata['service_type'] or service_type is None:
                if parameter in svc_metadata['parameters'] or parameter is None:
                    svc_metadata.update({'name': name})
                    services[name] = svc_metadata

    if not metadata:
        services = sorted(services.keys())

    return services


@dispatcher.add_method
def add_service(uri):
    """Add a custom web service created from a file or http folder

    Converts a local/network or http folder that contains a dsl.yml
    and associated data into a service that can be accessed through dsl
    """
    valid = False
    if uri.startswith('http'):
        url = uri.rstrip('/') + '/dsl.yml'
        r = requests.head(url)
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
def delete_service(uri):
    """Remove 'user' service."""
    user_services = util.get_settings()['USER_SERVICES']
    if uri in user_services:
        user_services.remove(uri)
        util.update_settings({'USER_SERVICES': user_services})
        util.save_settings()
        msg = 'service removed'
    else:
        msg = 'service not found'

    return msg
