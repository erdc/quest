"""API functions related to data Filters.

This will eventually hold filter related functionality
"""
from .. import util
from jsonrpc import dispatcher
from .metadata import get_metadata
from pint import UnitRegistry
from .tasks import add_async


@dispatcher.add_method
def get_filters(filters=None, expand=False, **kwargs):

    """List available filter plugins
    Parameters
    ----------
        filters (dict):
            optional kwargs filter the list of filters
            allowed filters are dataset, group, datatype, geotype, parameter
            if dataset is used it overides the others and sets them from the
            dataset metadata.

        metadata: bool (default False)
            If true return a dict of metadata

    Return
    ------
        available filters (list or dict)

    Examples:

        In [1]: import dsl
        In [2]: dsl.api.get_filters(filters={'group':'Raster'})
        Out[2]: ['get-elevations-along-path', 'export-raster']

        In [3]: dsl.api.get_filters(filters={'group':'Terrain'})
        Out[3]: ['vitd2nrmm', 'ffd2nrmm']

        In [4]: dsl.api.get_filters(filters={'group':'Timeseries'})
        Out[4]: ['ts-resample', 'ts-remove-outliers']

        In [5]: dsl.api.get_filters(filters={'datatype':'timeseries', 'parameters': 'streamflow'})
        Out[5]: ['ts-resample', 'ts-remove-outliers']

        In [6]: dsl.api.get_filters(filters={'dataset': 'd086ecbbb71947509493f785177b60be'})
        Out[6]: ['ts-resample', 'ts-remove-outliers']

        In [7]: dsl.api.get_filters(filters={'dataset': 'd086ecbbb71947509493f785177b60be'}, metadata=True)
        Out[7]:
        {'ts-remove-outliers': {'group': 'Timeseries',
          'operates_on': {'datatype': ['timeseries'],
           'geotype': None,
           'parameters': None},
          'produces': {'datatype': ['timeseries'],
           'geotype': None,
           'parameters': None}},
         'ts-resample': {'group': 'Timeseries',
          'operates_on': {'datatype': ['timeseries'],
           'geotype': None,
           'parameters': None},
          'produces': {'datatype': ['timeseries'],
           'geotype': None,
           'parameters': None}}}
    """
    avail = [dict(name=k, **v.metadata) for k,v in util.load_drivers('filters').items()]

    if filters is not None:
        for k, v in filters.items():
            if k == 'dataset':
                m = get_metadata(v).get(v)
                kwargs['datatype'] = m.get('datatype')
                kwargs['parameters'] = m.get('parameter')
                feature = m.get('feature')
                kwargs['geometry'] = get_metadata(feature).get(feature).get('geometry')
                return get_filters(filters=kwargs, expand=expand)
            elif k == 'group':
                avail = [f for f in avail if v == f['group']]
            else:
                avail = [f for f in avail if f['operates_on'][k] is None or v in f['operates_on'][k]]

    if expand:
        avail = {f.pop('name'): f for f in avail}
    else:
        avail = [f['name'] for f in avail]

    return avail


@dispatcher.add_method
@add_async
def apply_filter(name, datasets=None, features=None, options=None, as_dataframe=None, expand=None):
    """Apply Filter to dataset."""
    datasets = util.listify(datasets)
    features = util.listify(features)
    options = util.listify(options)

    driver = util.load_drivers('filters', name)[name].driver
    result = driver.apply_filter(datasets, features, options)

    new_datasets = util.listify(result.get('datasets', []))
    new_features = util.listify(result.get('features', []))

    if expand or as_dataframe:
        new_datasets = get_metadata(new_datasets, as_dataframe=True)
        new_features = get_metadata(new_features, as_dataframe=True)

        if expand:
            new_datasets = list(new_datasets.to_dict(orient='index').values())
            new_features = util.to_geojson(new_features)['features']

    result.update({'datasets': new_datasets, 'features': new_features})

    return result


@dispatcher.add_method
def apply_filter_options(name, fmt='json-schema'):
    """Retreive kwarg options for apply_filter."""
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter_options(fmt)
