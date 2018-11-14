import param

from .datasets import open_dataset
from .metadata import get_metadata
from .tasks import add_async
from ..util import to_geojson
from ..static import UriType, PluginType
from ..plugins.plugins import load_plugins


def get_tools(filters=None, expand=False, **kwargs):

    """List available tool plugins

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
        tools (list or dict, Default=list):
            all available tools

    """
    avail = [dict(name=k, **v.metadata) for k, v in load_plugins(PluginType.TOOL).items()]

    if filters is not None:
        for k, v in filters.items():
            if k == 'dataset':
                m = get_metadata(v).get(v)
                kwargs['datatype'] = m.get('datatype')
                kwargs['parameters'] = m.get('parameter')
                catalog_entry = m.get('catalog_entry')
                geometry = get_metadata(catalog_entry).get(catalog_entry).get('geometry')
                if geometry is not None:
                    kwargs['geotype'] = geometry.geom_type
                return get_tools(filters=kwargs, expand=expand)
            elif k == 'group':
                avail = [f for f in avail if v == f['group']]
            else:
                avail = [f for f in avail if f['operates_on'][k] is None or v in f['operates_on'][k]]

    if expand:
        avail = {f.pop('name'): f for f in avail}
    else:
        avail = [f['name'] for f in avail]

    return avail


@add_async
def run_tool(name, options=None, as_dataframe=None, expand=None, as_open_datasets=None, **kwargs):
    """Apply Tool to dataset.

    Args:
        name (string,Required):
            name of filter
        options (dict, Required):
            a dictionary of arguments to pass to the filter formatted as specified by `get_tool_options`
        expand (bool, Optional, Default=False):
            include details of newly created dataset and format as a dict
        as_dataframe (bool, Optional, Default=False):
            include details of newly created dataset and format as a pandas dataframe
        as_open_datasets (bool, Optional, Default=False):
            returns datasets as Python data structures rather than Quest IDs
        async (bool,Optional):
            if True, run filter in the background
        kwargs:
            keyword arguments that will be added to `options`


    Returns:
        dataset/catalog_entry uris (dict or pandas dataframe, Default=dict):
             resulting datasets and/or catalog_entries


    """
    if isinstance(options, param.Parameterized):
        options = dict(options.get_param_values())
    options = options or dict()
    options.update(kwargs)

    plugin = load_plugins(PluginType.TOOL, name)[name]
    result = plugin.run_tool(**options)

    new_datasets = result.get('datasets', [])
    new_catalog_entries = result.get('catalog_entries', [])

    if expand or as_dataframe:
        new_datasets = get_metadata(new_datasets, as_dataframe=True)
        new_catalog_entries = get_metadata(new_catalog_entries, as_dataframe=True)

        if expand:
            new_datasets = list(new_datasets.to_dict(orient='index').values())
            new_catalog_entries = to_geojson(new_catalog_entries)['catalog_entries']

    result.update({'datasets': new_datasets, 'catalog_entries': new_catalog_entries})

    if as_open_datasets:
        result['datasets'] = [open_dataset(dataset) for dataset in result['datasets']]

    return result


def get_tool_options(name, fmt='json', **kwargs):
    """Retrieve kwarg options for run_tool.

    Args:
        name (string, Required):
            name of filter
        fmt (string, Required, Default='json'):
            format in which to return options. One of ['json', 'param']
        kwargs:
            keyword arguments of options to set and exclude from return value.
    Returns:
        tool options (json scheme):
            tool options that can be applied when calling quest.api.run_filter
    """
    plugin = load_plugins(PluginType.TOOL, name)[name]
    return plugin.get_tool_options(fmt, **kwargs)
