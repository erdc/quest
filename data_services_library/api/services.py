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
            datasets.append({'id': name})

    return datasets


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


@util.jsonify
def get_locations(service_name, features=None, **kwargs):
    """Fetches location data for a given source (points, lines, polygons)
    """
    service = util.load_drivers('services', service_name)[service_name].driver

    if features:
        return  service.get_feature_locations(features, **kwargs)
    
    return service.get_locations(**kwargs)
