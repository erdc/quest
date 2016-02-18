"""API functions related to Services.

Providers are inferred by aggregating information from service plugins.
"""
from __future__ import absolute_import
from __future__ import print_function
from builtins import str
from jsonrpc import dispatcher
from .. import util
from stevedore import driver


@dispatcher.add_method
def get_providers():
    """Return list of Providers."""
    providers = util.load_drivers('services')
    return {k: v.metadata for k, v in providers.iteritems()}


@dispatcher.add_method
def get_services(parameter=None, service_type=None):
    """Return list of Services."""
    providers = util.load_drivers('services')
    services = {}
    for provider, svc in providers.iteritems():
        for service, metadata in svc.get_services().iteritems():
            name = 'service://%s:%s' % (provider, service)
            if service_type == metadata['service_type'] or service_type is None:
                if parameter in metadata['parameters'] or parameter is None:
                    services[name] = metadata

    return services


@dispatcher.add_method
def new_service():
    """Create a new DSL service from 'user' collection/website etc.

    SHOULD THIS BE CALLED ADD_SERVICE
    """
    pass


@dispatcher.add_method
def update_service():
    """Update 'user' service metadata or path."""
    pass


@dispatcher.add_method
def delete_service():
    """Remove 'user' service."""
    pass


def _load_services(names=None):
    settings = util.get_settings()
    # add web services
    web_services = util.list_drivers('services')
    web_services.remove('local')
    enabled_services = settings.get('WEB_SERVICES', [])
    if len(enabled_services) > 0:
        web_services = list(set(web_services).intersection(enabled_services))

    services = {name: driver.DriverManager('dsl.services', name, invoke_on_load='True').driver for name in web_services}

    if len(settings.get('LOCAL_SERVICES', [])) > 0:
        for path in settings.get('LOCAL_SERVICES', []):
            try:
                drv = driver.DriverManager('dsl.services', 'local', invoke_on_load='True', invoke_kwds={'path': path}).driver
                services['local-' + drv.name] = drv
            except Exception as e:
                print('Failed to load local service from %s, with exception: %s' % (path, str(e)))

    if names is not None:
        services = {k: v for k, v in services.items() if k in names}

    return services
