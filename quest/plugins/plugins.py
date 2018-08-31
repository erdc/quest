from .base import ProviderBase, IoBase, ToolBase
from ..util import listify, get_settings
import importlib
import inspect
import pkgutil
import logging
logger = logging.getLogger('quest')

plugin_instances = {
    'provider': None,
    'io': None,
    'tool': None,
}

plugin_namespaces = {
    'provider': 'quest_provider_plugins',
    'io': 'quest_io_plugins',
    'tool': 'quest_tool_plugins',
}

plugin_base_classes = {
    'provider': ProviderBase,
    'io': IoBase,
    'tool': ToolBase,
}

plugin_instantiate_funcs = {
    'provider': lambda x: x(),
    'io': lambda x: x(),
    'tool': lambda x: x.instance(),
}


def list_plugins(namespace):
    """Get a specific list of avaliable plugins.

    Args:
        namespace (str): Key for what type of plugins that you want.

    Returns:
        A list of plugin names.

    """
    if plugin_instances[namespace] is None:
        load_plugins(namespace)

    return list(plugin_instances[namespace].keys())


def load_plugins(namespace, names=None):
    """Loads a specific kind a of plugin.

    Notes:
        Only key/value pairs that are provided are updated,
        any other existing pairs are left unchanged or defaults
        are used.

    Args:
        namespace (str): Key for what type of plugins that you want.
        names (list): A list of plugin names to load.

    Returns:
        A dictionary of plugins with the name as the key, and the object as the value.

    """
    global plugin_instances

    names = listify(names)
    plugin_dict = {}
    plugin_module = importlib.import_module(plugin_namespaces[namespace])
    get_object = plugin_instantiate_funcs[namespace]
    for _, modname, ispkg in pkgutil.iter_modules(plugin_module.__path__):
        try:
            plugin_name = plugin_namespaces[namespace] + '.' + modname
            plugin_module = importlib.import_module(plugin_name)
            for name, cls in inspect.getmembers(plugin_module, inspect.isclass):
                if issubclass(cls, plugin_base_classes[namespace]) and cls.__module__.startswith(plugin_name):
                    obj = get_object(cls)
                    if names is None or obj.name in names:
                        plugin_dict[obj.name] = obj
        except Exception as e:
            logger.error('{} plugin, {} has failed to load, '
                         'due to the following exception: \n{} {}.'
                         .format(namespace, modname, e.__class__.__name__, str(e)))
            continue

    plugin_instances[namespace] = plugin_dict
    return plugin_dict


def load_providers(update_cache=False):
    """Get the settings currently being used by QUEST.

    Args:
        update_cache (bool): A switch to update the plugins.

    Returns:
        A dictionary of plugins with the name as the key, and the object as the value.

    """
    global plugin_instances

    settings = get_settings()

    if update_cache or plugin_instances['provider'] is None:
        providers = load_plugins('provider')
        if len(settings.get('USER_SERVICES', [])) > 0:
            from quest.plugins import user_provider
            for uri in settings.get('USER_SERVICES', []):
                try:
                    plugin = user_provider.UserProvider(uri=uri)
                    providers[plugin.name] = plugin
                except Exception as e:
                    logger.error('{} plugin, {} has failed to load, '
                                 'due to the following exception: \n\t{} {}.'
                                 .format('user', uri, e.__class__.__name__, str(e)))

        plugin_instances['provider'] = providers
    else:
        providers = plugin_instances['provider']

    return providers
