import param
import quest
from abc import ABCMeta, abstractmethod
from functools import partial


class AbstractParameterized(param.parameterized.ParameterMetaclass, ABCMeta): pass


class QuestSelector(param.ObjectSelector, metaclass=AbstractParameterized):
    __slots__ = ['filters', 'queries']

    def __init__(self, filters=None, queries=None, **params):
        self.filters = filters
        self.queries = queries
        params['check_on_set'] = False
        super(QuestSelector, self).__init__(**params)

    @property
    @abstractmethod
    def quest_entities(self):
        pass

    def get_range(self):
        self.names = self.quest_entities
        self.objects = list(self.names.values())
        return super(QuestSelector, self).get_range()


class DatasetSelector(QuestSelector):
    @property
    def quest_entities(self):
        datasets = quest.api.get_datasets(
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return {v['display_name']: k for k, v in datasets.items()}


class CatalogEntrySelector(QuestSelector):
    @property
    def quest_entities(self):
        catalog_entries = quest.api.search_catalog(
            quest.api.get_collections(),
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return {v['display_name']: k for k, v in catalog_entries.items()}


class DatasetListSelector(QuestSelector, param.ListSelector):
    @property
    def quest_entities(self):
        datasets = quest.api.get_datasets(
            filters=self.filters,
            queries=self.queries,
            expand=True
        )
        return {v['display_name']: k for k, v in datasets.items()}


class AbstractQuestSelectorParameterized(param.parameterized.ParameterizedMetaclass, ABCMeta): pass


class QuestEntitySelector(param.Parameterized, metaclass=AbstractQuestSelectorParameterized):
    @property
    @abstractmethod
    def get_quest_entities(self):
        return None

    @property
    def entity_name(self):
        return 'value'

    def __init__(self, default=None):
        entities = self.get_quest_entities()
        entity_param = self.param[self.entity_name]
        entity_param.names = {v['display_name']: k for k, v in entities.items()}
        entity_param.objects = list(entity_param.names.values())
        entity_param.default = default or entity_param.objects[0]
        super().__init__(name='')


class ProviderSelector(QuestEntitySelector):
    value = param.ObjectSelector(default=None, objects=[])

    # @property
    # def entity_name(self):
    #     return 'provider'

    @property
    def get_quest_entities(self):
        return partial(quest.api.get_providers, expand=True)


class PublisherSelector(QuestEntitySelector):
    value = param.ObjectSelector(default=None, objects=[])

    # @property
    # def entity_name(self):
    #     return 'publisher'

    @property
    def get_quest_entities(self):
        return partial(quest.api.get_publishers, expand=True)


class ServiceSelector(QuestEntitySelector):
    value = param.ObjectSelector(default=None, objects=[])

    # @property
    # def entity_name(self):
    #     return 'service'

    @property
    def get_quest_entities(self):
        return partial(quest.api.get_services, parameter=self.parameter, service_type=self.service_type, expand=True)

    def __init__(self, parameter=None, service_type=None, default=None):
        self.parameter = parameter
        self.service_type = service_type
        super().__init__(default=default)


class ParameterSelector(QuestEntitySelector):
    value = param.ObjectSelector(default=None, objects=[])

    # @property
    # def entity_name(self):
    #     return 'parameter'

    @property
    def get_quest_entities(self):
        return lambda: {p: {'display_name': p} for p in quest.api.get_mapped_parameters()}


class CollectionSelector(QuestEntitySelector):
    value = param.ObjectSelector(default=None, objects=[])

    # @property
    # def entity_name(self):
    #     return 'collection'

    @property
    def get_quest_entities(self):
        return partial(quest.api.get_collections, expand=True)


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
    schema['name'] = pobj.name
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
                         and getattr(pobj, x.name) == x.default,  # Filter out parameters that are already set
                         pobj.param.objects().values()))

    if not params:
        return {}

    properties = [_param_to_json(p) for p in sorted(params, key=lambda p: p.precedence or 9999)]

    schema = {
        "title": pobj.title,
        "properties": properties,
    }
    return schema
