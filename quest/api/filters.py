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

    Args:
        filters (dict, Optional, Default=None):
            filter the list of filters by one or more of the available filters
            available filters:
                    dataset (string, Optional):
                    group (string, Optional)
                    geotype (string, Optional)
                    datatype (string, Optional)
                    parameter (string, Optional)
            if a dataset filter is used, all other filters are overridden and set from the dataset's metadata.
        expand (bool, Optional, Default=None):
            if True, return details of the filters as a dict
        kwargs:
            optional filter kwargs


    Returns:
        filters (list or dict, Default=list):
            all available filters

    """
    avail = [dict(name=k, **v.metadata) for k,v in util.load_drivers('filters').items()]

    if filters is not None:
        for k, v in filters.items():
            if k == 'dataset':
                m = get_metadata(v).get(v)
                kwargs['datatype'] = m.get('datatype')
                kwargs['parameters'] = m.get('parameter')
                feature = m.get('feature')
                kwargs['geotype'] = get_metadata(feature).get(feature).get('geometry').geom_type
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
    """Apply Filter to dataset.

    Args:
        name (string,Required):
            name of filter
        datasets (string, list of strings, or dict, Required):
            datasets to which the filter is to be applied
        features (string, list of strings, or dict, Optional, Default=False)
            features to which the filter is to be applied
        expand (bool, Optional, Default=False):
            include details of newly created dataset and format as a dict
        as_dataframe (bool, Optional, Default=False):
            include details of newly created dataset and format as a pandas dataframe
        async (bool,Optional):
            if True, run filter in the background


    Returns:
        dataset/feature uris (dict or pandas dataframe, Default=dict):
             resulting datasets and/or features


    """
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
            new_datasets = new_datasets.to_dict(orient='index')
            new_features = new_features.to_dict(orient='index')

    result.update({'datasets': new_datasets, 'features': new_features})

    return result


@dispatcher.add_method
def apply_filter_options(name, fmt='json-schema'):
    """Retreive kwarg options for apply_filter.

    Args:
        name (string, Required):
            name of filter
        fmt (string, Required, Default='json-schema'):
            format in which to return options
    Returns:
        filter options (json-schema or smtk scheme):
            filter options that can be applied when calling quest.api.apply_filter
    """
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter_options(fmt)
