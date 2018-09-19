import param
import quest


class NamedString(object):
    def __init__(self, string, name):
        self.string = string
        self.name = name

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string


class DatasetSelector(param.ObjectSelector):
    __slots__ = ['filters', 'queries']

    def __init__(self, filters=None, queries=None, **params):
        self.filters = filters
        self.queries = queries
        super(DatasetSelector, self).__init__(**params)

    @property
    def datasets(self):
        datasets = quest.api.get_datasets(
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return [NamedString(k, v['display_name']) for k, v in datasets.items()]

    def get_range(self):
        self.objects = self.datasets
        return super(DatasetSelector, self).get_range()


class CatalogEntrySelector(param.ObjectSelector):
    __slots__ = ['filters', 'queries']

    def __init__(self, filters=None, queries=None, **params):
        self.filters = filters
        self.queries = queries
        super(CatalogEntrySelector, self).__init__(**params)

    @property
    def catalog_entries(self):
        catalog_entries = quest.api.search_catalog(
            quest.api.get_collections(),
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return [NamedString(k, v['display_name']) for k, v in catalog_entries.items()]

    def get_range(self):
        self.objects = self.catalog_entries
        return super(CatalogEntrySelector, self).get_range()


class DatasetListSelector(param.ListSelector):
    __slots__ = ['filters', 'queries']

    def __init__(self, filters=None, queries=None, **params):
        self.filters = filters
        self.queries = queries
        super(DatasetListSelector, self).__init__(**params)

    @property
    def datasets(self):
        datasets = quest.api.get_datasets(
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return [NamedString(k, v['display_name']) for k, v in datasets.items()]

    def get_range(self):
        self.objects = self.datasets
        return super(DatasetListSelector, self).get_range()


class Service(param.Parameterized):
    service = param.ObjectSelector(default=None, objects=[])

    def __init__(self, parameter=None, service_type=None):
        services = quest.api.get_services(parameter=parameter, service_type=service_type)
        service_param = self.params()['service']
        service_param.objects = services
        service_param.default = services[0]
        super().__init__(name='')


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
        schema['range'] = sorted(list(l) for l in pobj.get_range().items())

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
