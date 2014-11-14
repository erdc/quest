"""
    api definition
"""

from .config import available_services
from collections import defaultdict
import geojson
import json
import itertools
from stevedore import extension, driver
import os
import glob

SERVICES_NAMESPACE = 'data_services_library.services'
FILTERS_NAMESPACE = 'data_services_library.filters'


def download(uid, **kwargs):
    """downloads data from a given service and returns a reference to downloaded data
    """
    service = driver.DriverManager(SERVICES_NAMESPACE, uid, invoke_on_load='True')
    response = service.driver.download(**kwargs)

    return geojson.dumps(response, sort_keys=True)


def get_datasets(uid=None, as_json=False):
    """Get local datasets. 
    """
    demo_dir = os.getenv('DSL_DEMO_DIR')
    

    if uid:
        with open(os.path.join(demo_dir, 'datasets', uid + '.json')) as f:
            js = json.load(f)
    else:
        js = []
        for filename in glob.glob(os.path.join(demo_dir, 'datasets', '*.json')):
            root, ext = os.path.splitext(filename)
            uid = os.path.split(root)[-1]
            js.append({'id': uid})

    return json.dumps(js)


def get_providers(id=None, as_json=False):
    """ generates a list of available data providers
    """
    mgr = extension.ExtensionManager(
        namespace=SERVICES_NAMESPACE,
        invoke_on_load=True,
    )
    datasets = mgr.map(_metadata)

    providers = [dataset['provider'] for dataset in datasets]
    providers = {provider['id']:provider for provider in providers}.values()

    if id:
        providers = [provider for provider in providers if provider['id']==id]

    if as_json:
        return json.dumps(providers, sort_keys=True,
                          indent=4, separators=(',', ': '))

    return providers


def get_services(uid=None, as_json=False, group=False, provider=None):
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

    if provider:
        datasets = [dataset for dataset in datasets if dataset['provider']['id']==provider]

    if not group:
        services = sorted(datasets)
    else:
        #group by provider
        services = defaultdict(dict)
        for dataset in datasets:
            services[dataset['provider']['id']]['provider'] = {'id': dataset['provider']['id'], 'name': dataset['provider']['name']}
            try:
                services[dataset['provider']['id']]['services'].append(_remove_key(dataset, 'provider'))    
            except:
                services[dataset['provider']['id']]['services'] = []
                services[dataset['provider']['id']]['services'].append(_remove_key(dataset, 'provider'))

        services = sorted(services.values())

    if as_json:
        return json.dumps(services, sort_keys=True,
                          indent=4, separators=(',', ': '))

    return services


def get_filters(uid=None, as_json=False, group=False, datatype=None):
    """ generates a list of available data services
    """

    if uid:
        filters = driver.DriverManager(FILTERS_NAMESPACE, uid, invoke_on_load='True')
        datasets = [_metadata(filters.extensions[0])]
    else:
        mgr = extension.ExtensionManager(
            namespace=FILTERS_NAMESPACE,
            invoke_on_load=True,
        )
        datasets = mgr.map(_metadata)


    if datatype:
        datasets = [dataset for dataset in datasets if dataset['type']==datatype]

    if not group:
        filters = sorted(datasets)
    else:
        #rearrange by geotype
        filters = [{
                        'type': name,
                        'filters': [_remove_key(item, 'type') for item in group],
                    } for name, group in itertools.groupby(sorted(datasets), 
                                                           lambda p:p['type'])]

    if as_json:
        return json.dumps(filters, sort_keys=True,
                          indent=4, separators=(',', ': '))

    return filters


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
