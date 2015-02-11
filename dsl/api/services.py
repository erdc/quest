"""API functions related to Services

Providers are inferred by aggregating information from service plugins.
"""
from __future__ import absolute_import
import json
import os
import glob
from .. import util
from collections import defaultdict


@util.jsonify
def get_data(name, locations, **kwargs):
    """downloads data from a given service and returns a reference to downloaded data
    """
    service = util.load_drivers('services', name)[name]
    return service.driver.get_data(locations, **kwargs)


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
def get_parameters(name):
    service = util.load_drivers('services', name)[name].driver

    return service.provides()


@util.jsonify
def get_services(names=None, group=False, provider=None, **kwargs):
    """ generates a list of available data services
    """

    services = [dict(service_code=k, parameters=v.provides(), **v.metadata) for k,v in util.load_drivers('services', names=names).iteritems()]

    if provider:
        services = [service for service in services if service['provider']['code']==provider]

    if not group:
        services = sorted(services)
    else:
        #group by provider
        grouped = defaultdict(dict)
        for service in services:
            grouped[service['provider']['abbr']]['provider'] = {'abbr': service['provider']['abbr'], 'name': service['provider']['name']}
            try:
                grouped[service['provider']['abbr']]['services'].append(util.remove_key(service, 'provider'))    
            except:
                grouped[service['provider']['abbr']]['services'] = []
                grouped[service['provider']['abbr']]['services'].append(util.remove_key(service, 'provider'))

        services = sorted(grouped.values())

    return services


@util.jsonify
def get_locations(service_name, locations=None, **kwargs):
    """Fetches location data for a given source (points, lines, polygons)
    """
    service = util.load_drivers('services', service_name)[service_name].driver
    
    return service.get_locations(locations=locations, **kwargs)
