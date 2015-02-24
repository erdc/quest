"""API functions related to data Filters

This will eventually hold filter related functionality 
"""
from .. import util

@util.jsonify
def get_filters(names=None, group=False, datatype=None, **kwargs):
    """List available filter plugins
    """
    names = util.listify(names)
    filters = [dict(name=k, **v.metadata) for k,v in util.load_drivers('filters', names=names).iteritems()]

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


@util.jsonify
def apply_filter(name, **kwargs):
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter(**kwargs)


@util.jsonify
def apply_filter_options(name, **kwargs):
    driver = util.load_drivers('filters', name)[name].driver
    return driver.apply_filter_options()
