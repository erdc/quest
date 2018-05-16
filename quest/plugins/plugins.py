import importlib
import inspect
import pkgutil
import logging
from .base import ProviderBase, IoBase, FilterBase
from ..util import listify, get_settings
logger = logging.getLogger('quest')

the_providers = None

the_plugins = {'provider': 'quest_provider_plugins',
               'io': 'quest_io_plugins',
               'filters': 'quest_filter_plugins',
               }

the_plugin_classes = {'provider': ProviderBase,
                      'io': IoBase,
                      'filters': FilterBase,
                      }


def list_plugins(namespace):

    plugin_module = importlib.import_module(the_plugins[namespace])

    return [modname for _, modname, iskpg in pkgutil.iter_modules(plugin_module.__path__)]


def load_plugins(namespace, names=None):
    names = listify(names)
    plugin_dict = {}
    plugin_module = importlib.import_module(the_plugins[namespace])
    for _, modname, ispkg in pkgutil.iter_modules(plugin_module.__path__):
        try:
            plugin_name = the_plugins[namespace] + '.' + modname
            plugin_module = importlib.import_module(plugin_name)
            for name, obj in inspect.getmembers(plugin_module, inspect.isclass):
                if issubclass(obj, the_plugin_classes[namespace]) and obj.__module__.startswith(plugin_name):
                    if names is None or obj.name in names:
                        plugin_dict[obj.name] = obj()
        except Exception as e:
            logger.error('{} plugin, {} has failed to load, '
                         'due to the following exception: \n{} {}.'
                         .format(namespace, modname, e.__class__.__name__, str(e)))
            continue

    return plugin_dict


def load_providers(update_cache=False):
    global the_providers

    settings = get_settings()

    if update_cache or the_providers is None:
        providers = load_plugins('provider')
        if len(settings.get('USER_SERVICES', [])) > 0:
            from quest.plugins import user_provider
            for uri in settings.get('USER_SERVICES', []):
                try:
                    plugin = user_provider.UserProvider(uri=uri)
                    providers['user-' + plugin.name] = plugin
                except Exception as e:
                    logger.error('{} plugin, {} has failed to load, '
                                 'due to the following exception: \n\t{} {}.'
                                 .format('user', uri, e.__class__.__name__, str(e)))

        the_providers = providers
    else:
        providers = the_providers

    return providers