"""API functions related to data Filters

This will eventually hold filter related functionality 
"""
from .. import util

@util.jsonify
def get_filters(names=None, group=False, datatype=None, **kwargs):
    """List available filter plugins
    """

    filters = [v.metadata for v in util.load_drivers('filters', names=names).itervalues()]

    if datatype:
        filters = [f for f in filters if f['type']==datatype]

    if not group:
        filters = sorted(datasets)
    else:
        #rearrange by geotype
        filters = [{
                        'type': name,
                        'filters': [_remove_key(item, 'type') for item in group],
                    } for name, group in itertools.groupby(sorted(filters), 
                                                           lambda p:p['type'])]

    return filters


@util.jsonify
def apply_filter(names, **kwargs):
    pass
