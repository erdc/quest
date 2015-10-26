"""API functions related to data Filters

This will eventually hold filter related functionality 
"""
from .. import util
from jsonrpc import dispatcher


@dispatcher.add_method
def get_filters(names=None, group=False, datatype=None, level=None, **kwargs):
    """List available filter plugins
    """
    names = util.listify(names)
    filters = [dict(name=k, **v.metadata) for k,v in util.load_drivers('filters', names=names).items()]

    if datatype is not None:
        filters = [f for f in filters if datatype in f['operates_on']['datatype']]

    if level is not None:
        filters = [f for f in filters if level in f['operates_on']['level']]

    if not group:
        filters = sorted(filters)
    else:
        #rearrange by geotype
        filters = [{
                        'type': name,
                        'filters': [_remove_key(item, 'type') for item in group],
                    } for name, group in itertools.groupby(sorted(filters), 
                                                           lambda p:p['type'])]

    return filters


@dispatcher.add_method
def apply_filter(name, **kwargs):
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter(**kwargs)


@dispatcher.add_method
def apply_filter_options(name, **kwargs):
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter_options()
