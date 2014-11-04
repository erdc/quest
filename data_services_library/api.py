"""
    api definition
"""

from .config import available_services
import geojson
import json
import itertools
from stevedore import extension, driver

SERVICES_NAMESPACE = 'data_services_library.services'


def get_services(uid=None, as_json=False, group=True):
    """ generates a list of available data services
    """

    if uid:
        service = driver.DriverManager(SERVICES_NAMESPACE, uid, invoke_on_load='True')
        datasets = [_metadata(service.extensions[0])]
    else:
        mgr = extension.ExtensionManager(
            namespace=SERVICES_NAMESPACE,
            invoke_on_load=True,
        )
        datasets = mgr.map(_metadata)

    if not group:
        services = sorted(datasets)
    else:
        #rearrange by service name
        services = [{
                        'service_name': name,
                        'datasets': [_remove_key(item, 'service_name') for item in group],
                    } for name, group in itertools.groupby(sorted(datasets), 
                                                           lambda p:p['service_name'])]

    if as_json:
        return json.dumps(services, sort_keys=True,
                          indent=4, separators=(',', ': '))

    return services


def add_source(source_name, source_type, metadata):
    """Add source to data services library
    """
    pass


def edit_source(source_name, source_type, metadata):
    """modify a source in the data services library
    """
    pass


def delete_source(source_name):
    """Delete a source from data services library
    """
    pass


def get_locations(service_uid, **kwargs):
    """Fetches location data for a given source (points, lines, polygons)
    """
    service = driver.DriverManager(SERVICES_NAMESPACE, service_uid, invoke_on_load='True')
    locations = service.driver.get_locations(**kwargs)

    return geojson.dumps(locations, sort_keys=True)


def get_data(source, identifiers, **kwargs):
    """Fetches data for a list of identifiers. Not sure what the kwargs 
    should be yet
    """
    pass


def get_available_filters(source_type):
    """Fetches list of available filters for the source source_type
    """
    pass


def get_filter(filter_name):
    """Fetches requires params for filter, may be able to combine this 
    with get_available_filters, by returning a dictionary
    """
    pass


def apply_filter(dataset, filter):
    """Apply filter to dataset
    """
    pass


def _metadata(ext):
    metadata = ext.obj.metadata.copy()
    metadata['uid'] = ext.name

    return metadata


def _remove_key(d, key):
    r = dict(d)
    del r[key]
    return r
