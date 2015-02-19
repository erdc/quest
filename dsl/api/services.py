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
def get_data(name, locations, parameters=None, **kwargs):
    """downloads data from a given service and returns a reference to downloaded data

    Parameters
    ----------
    name : str,
        The name of the service to be used
    locations : str or list of str,
        Comma separated list of location codes to retrieve data from
    parameters : ``None`` or str
        Comma separated list of parameters to download data for, if ``None``
        get all available parameters

    Note:
        additional kwargs (keyword arguments) are passed along to the plugins

    Returns
    -------
    data_files : dict,
        A python dict representation of the downloaded data file locations keyed by
        location and parameter.
    """
    locations = util.listify(locations)
    parameters = util.listify(parameters)
    service = util.load_drivers('services', name)[name]
    return service.driver.get_data(locations, parameters=parameters, **kwargs)


@util.jsonify
def get_data_filters(name, **kwargs):
    """get available filter options for get_data call

    Parameters
    ----------
    name : str,
        The name of the service to be used

    Returns
    -------
    schema : dict,
        A python representation of a json-schema
    """
    service = util.load_drivers('services', name)[name]
    return service.driver.get_data_filters()


@util.jsonify
def get_locations_filters(name, **kwargs):
    """get available filter options for get_locations call

    Parameters
    ----------
    name : str,
        The name of the service to be used

    Returns
    -------
    schema : dict,
        A python representation of a json-schema
    """
    service = util.load_drivers('services', name)[name]
    return service.driver.get_locations_filters()


@util.jsonify
def get_parameters(name, **kwargs):
    """get list of available parameters for a service

    Parameters
    ----------
    name : str,
        The name of the service to be used

    Returns
    -------
    parameters : list of str,
        list of parameters available
    """
    service = util.load_drivers('services', name)[name].driver
    return service.provides()


@util.jsonify
def get_services(names=None, group=False, provider=None, **kwargs):
    """get metadata for available data services

    Parameters
    ----------
    names : ``None`` or list of str,
        List of names of the services to be fetched

    group : bool,
        If True, group the metadata by provider. Default is False.

    provider : ``None`` or str,
        Filter list by provider. 

    Returns
    -------
    services : list of dict,
        list of services metadata
    """
    names = util.listify(names)
    services = [dict(service_code=k, parameters=v.provides(), **v.metadata) for k,v in util.load_drivers('services', names=names).iteritems()]

    if provider is not None:
        services = [service for service in services if service['provider']['code']==provider]

    if group is False:
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
def get_locations(name, locations=None, bounding_box=None, **kwargs):
    """Fetches location metadata for a given service

    Parameters
    ----------
    name: str,
        names of the service to be queried

    locations : ``None`` or str,
        comma separated list of location codes to fetch

    bounding_box : ``None or str,
        comma delimited set of 4 numbers

    Note: 
        Additional kwargs are passed through to plugins
        bounding_box is ignored when locations are passed

    Returns
    -------
    feature_collection : dict,
        a python dict representation of a geojson feature collection,
    """
    locations = util.listify(locations)
    bounding_box = util.listify(bounding_box)
    service = util.load_drivers('services', name)[name].driver
    
    return service.get_locations(locations=locations, bounding_box=bounding_box, **kwargs)
