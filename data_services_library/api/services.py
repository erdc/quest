"""
    api definition
"""

from __future__ import absolute_import
import geojson
import json
import itertools
from stevedore import extension, driver
import os
import glob
from .. import util
from collections import defaultdict

SERVICES_NAMESPACE = 'data_services_library.services'
FILTERS_NAMESPACE = 'data_services_library.filters'


@util.jsonify
def download(name, **kwargs):
    """downloads data from a given service and returns a reference to downloaded data
    """
    service = util.load_drivers('services', name)
    return service.driver.download(**kwargs)


@util.jsonify
def get_datasets(name=None):
    """Get local datasets. 
    """

    demo_dir = util.get_dsl_demo_dir()

    if name:
        with open(os.path.join(demo_dir, 'datasets', name + '.json')) as f:
            datasets = json.load(f)
    else:
        datasets = []
        for filename in glob.glob(os.path.join(demo_dir, 'datasets', '*.json')):
            root, ext = os.path.splitext(filename)
            name = os.path.split(root)[-1]
            datasets.append({'id': uid})

    return name


@util.jsonify
def get_services(names=None, group=False, provider=None, **kwargs):
    """ generates a list of available data services
    """

    services = [v.metadata for v in util.load_drivers('services', names=names).itervalues()]

    if provider:
        services = [service for service in services if service['provider']['id']==provider]

    if not group:
        services = sorted(services)
    else:
        #group by provider
        grouped = defaultdict(dict)
        for service in services:
            grouped[service['provider']['id']]['provider'] = {'id': service['provider']['id'], 'name': service['provider']['name']}
            try:
                grouped[service['provider']['id']]['services'].append(_remove_key(service, 'provider'))    
            except:
                grouped[service['provider']['id']]['services'] = []
                grouped[service['provider']['id']]['services'].append(_remove_key(service, 'provider'))

        services = sorted(grouped.values())

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


def get_locations(service_uid, as_json=True, features=None, **kwargs):
    """Fetches location data for a given source (points, lines, polygons)
    """
    service = driver.DriverManager(SERVICES_NAMESPACE, service_uid, invoke_on_load='True')

    if features:
        locations = service.driver.get_feature_locations(features, **kwargs)
    else:
        locations = service.driver.get_locations(**kwargs)

    if as_json==False:
        return locations

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
