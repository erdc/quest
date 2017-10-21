import json

import param

import quest
from .misc import to_json_default_handler


class DatasetSelector(param.ObjectSelector):
    __slots__ = ['filters']

    def __init__(self, filters=None, **params):
        self.filters = filters
        super(DatasetSelector, self).__init__(**params)

    @property
    def datasets(self):
        # ds = quest.api.get_datasets(filters=self.filters, as_dataframe=True)
        # return ds.display_name.to_dict()
        return quest.api.get_datasets(filters=self.filters)

    def get_range(self):
        self.objects = self.datasets
        return super(DatasetSelector, self).get_range()


class FeatureSelector(param.ObjectSelector):
    __slots__ = ['filters']

    def __init__(self, filters=None, **params):
        self.filters = filters
        super(FeatureSelector, self).__init__(**params)

    @property
    def features(self):
        return quest.api.get_features(quest.api.get_collections(), filters=self.filters)

    def get_range(self):
        self.objects = self.features
        return super(FeatureSelector, self).get_range()


class DatasetListSelector(param.ListSelector):
    __slots__ = ['filters']

    def __init__(self, filters=None, **params):
        self.filters = filters
        super(DatasetListSelector, self).__init__(**params)

    @property
    def datasets(self):
        return quest.api.get_datasets(filters=self.filters)

    def get_range(self):
        self.objects = self.datasets
        return super(DatasetListSelector, self).get_range()


# PARM to JSON functions


def _get_pobj_default(pobj):
    default = pobj.default
    if pobj.default is not None:
        if callable(pobj.default):
            default = pobj.default()
        else:
            default = pobj.default

        # default = json.dumps(default, default=to_json_default_handler)

    return default


def _param_to_json(pobj):
    schema = dict()
    schema['name'] = pobj._attrib_name
    schema['type'] = pobj.__class__.__name__
    schema['description'] = pobj.doc
    schema['default'] = _get_pobj_default(pobj)
    if hasattr(pobj, 'softbounds'):
        schema['bounds'] = pobj.softbounds
    if hasattr(pobj, 'get_range'):
        schema['range'] = sorted(list(l) for l in pobj.get_range().items())  # convert each tuple to a list for RPC

    return schema


def format_json_options(pobj):
    params = list(filter(lambda x: (x.precedence is None or x.precedence >= 0) and not x.constant
                         and getattr(pobj, x._attrib_name) == x.default,  # Filter out parameters that are already set
                         pobj.params().values()))

    if not params:
        return {}

    properties = [_param_to_json(p) for p in sorted(params, key=lambda p: p.precedence or 9999)]

    schema = {
        "title": pobj.title,
        "properties": properties,
    }
    return schema
