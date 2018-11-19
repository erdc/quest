import os
import requests

from ..plugins import load_providers
from ..database.database import get_db, db_session
from ..util import save_settings, get_settings, update_settings, parse_service_uri


def get_providers(expand=None, update_cache=False):
    """Return list of Providers.

    Args:
        expand (bool, Optional, Default=None):
            include providers' details and format as dict
        update_cache (bool, Optional, Default=False):
            reload the list of providers
    Returns:
        providers (list or dict, Default=list):
            list of all available providers

    """
    providers = load_providers(update_cache=update_cache)
    p = {k: v.metadata for k, v in providers.items()}
    if not expand:
        p = sorted(p.keys())

    return p


def get_services(expand=None, parameter=None, service_type=None):
    """Return list of Services.

    Args:
         expand (bool, Optional, Default=False):
            include providers' details and format as dict
         parameter (string, Optional, Default=None):
         service_type (string, Optional, Default=None'):
            filter to only include specific type

    Returns:
          providers (list or dict, Default=dict):
            all available providers

    """
    providers = load_providers()
    services = {}
    for provider_name, provider in providers.items():
        for service, svc_metadata in provider.get_services().items():
            name = 'svc://%s:%s' % (provider_name, service)
            if service_type == svc_metadata['service_type'] or service_type is None:
                if parameter in svc_metadata['parameters'] or parameter is None:
                    svc_metadata.update({'name': name})
                    services[name] = svc_metadata

    if not expand:
        services = sorted(services.keys())

    return services


def get_publishers(expand=None, publisher_type=None):
    """This method returns a list of avaliable publishers.

    The method first gets a dictionary filled with the available providers
    in Quest. Then we loop through grabbing the keys and the objects within
    the dictionary. Then we loop again, accessing each service getting another
    dictionary with the provider as the key and the metadata as the values.
    Then we create a publish uri, and get the publisher class name for the
    service. We return a list of publishers.

    Args:
         expand (bool, Optional, Default=False):
            include providers' details and format as dict
         publisher_type (string, Optional, Default=None'):
            filter to only include specific type

    Returns:
        providers (list or dict,Default=list):
            list of all available providers
    """
    providers = load_providers()
    publishers = {}
    for provider, pub in providers.items():
        for publisher, pub_metadata in pub.get_publishers().items():
            name = 'pub://%s:%s' % (provider, publisher)
            if publisher_type == pub_metadata['publisher_type'] or publisher_type is None:
                pub_metadata.update({'name': name})
                publishers[name] = pub_metadata

    if not expand:
        publishers = sorted(publishers.keys())

    return publishers


def add_user_provider(uri):
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
        user_services = get_settings()['USER_SERVICES']
        if uri not in user_services:
            user_services.append(uri)
            update_settings({'USER_SERVICES': user_services})
            save_settings()
            msg = 'service added'
            load_providers(update_cache=True)
        else:
            msg = 'service already present'
    else:
        msg = 'service does not have a quest config file (quest.yml)'

    return msg


def delete_user_provider(uri):
    """Remove 'user' service.

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:
        message (string):
            status of deleting service

    """
    if uri.startswith('svc://'):
        provider, service, _ = parse_service_uri(uri)
        if not provider.startswith('user'):
            raise ValueError('Can only remove user providers')

        uri = get_providers(expand=True)[provider].get('service_uri')

    user_services = get_settings()['USER_SERVICES']
    if uri in user_services:
        user_services.remove(uri)
        update_settings({'USER_SERVICES': user_services})
        save_settings()
        msg = 'service removed'
        load_providers(update_cache=True)
    else:
        msg = 'service not found'

    return msg


def get_auth_status(uri):
    """Check to see if a provider has been authenticated

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:
        True on success
        False on not authenticated

    """
    db = get_db()
    with db_session:
        p = db.Providers.select().filter(provider=uri).first()

        if p is None:
            return False

    return True


def authenticate_provider(uri, **kwargs):
    """Authenticate the user.

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:


    """
    provider_plugin = load_providers()[uri]
    provider_plugin.authenticate_me(**kwargs)


def unauthenticate_provider(uri):
    """Un-Authenticate the user.

    Args:
        uri (string, Required):
            uri of 'user service'
     Returns:


    """
    driver = load_providers()[uri]
    driver.unauthenticate_me()










