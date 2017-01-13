"""Module wide settings.

"""

import appdirs
from jsonrpc import dispatcher
import logging
import os
import yaml

log = logging.getLogger(__name__)

settings = {}


@dispatcher.add_method
def get_settings():
    """Get the settings currently being used by DSL.

    Returns
    -------
        settings : dict
            Dictionary of current settings

    Example
    -------
    >>> dsl.api.get_settings()
    {'BASE_DIR': '/Users/dharhas/Library/Application Support/dsl',
    'CACHE_DIR': 'cache',
    'PROJECTS_DIR': 'projects',
    'USER_SERVICES': [],
    }
    """
    global settings
    if not settings:
        update_settings()
        filename = _default_config_file()
        if os.path.isfile(filename):
            update_settings_from_file(filename)

    return settings


@dispatcher.add_method
def update_settings(config={}):
    """Update settings currently being used by DSL

    Only key/value pairs that are provided are updated,
    any other existing pairs are left unchanged or defaults
    are used.

    Parameters
    ----------
        config : dict
            key/value pairs of settings that are to be updated.

    Returns
    -------
        True
            Settings where updated successfully

    Example
    -------
    >>> dsl.api.update_settings({'BASE_DIR':'/Users/dharhas/mydsldir'})
    {'BASE_DIR': '/Users/dharhas/mydsldir',
     'CACHE_DIR': 'cache',
     'PROJECTS_DIR': 'projects',
     'USER_SERVICES': [],
     }
    """

    global settings
    settings.update(config)
    settings.setdefault('BASE_DIR', _default_dsl_dir())
    settings.setdefault('CACHE_DIR', 'cache')
    settings.setdefault('PROJECTS_DIR', 'projects')
    settings.setdefault('USER_SERVICES', [])

    # initialize projects and reconnect to database in new BASE_DIR
    if 'BASE_DIR' in config.keys():
        from .. import init
        init()

    return True


@dispatcher.add_method
def update_settings_from_file(filename):
    """Update settings currently being used by DSL from a yaml file

    Only key/value pairs that are provided are updated,
    any other existing pairs are left unchanged or defaults
    are used.

    Parameters
    ----------
        filename : str
            path to yaml file containing settings

    Returns
    -------
        True
            Settings were updated successfully from file

    Example
    -------
    >>> dsl.api.update_settings_from_file('/Users/dharhas/mydslsettings.yml')
    {'BASE_DIR': '/Users/dharhas/mydsl2dir',
     'CACHE_DIR': 'cache',
     'PROJECTS_DIR': 'data',
     'USER_SERVICES': [],
     }
    """
    config = yaml.safe_load(open(filename, 'r'))

    # convert keys to uppercase
    config = dict((k.upper(), v) for k, v in config.items())

    # recursively parse for local services
    config['USER_SERVICES'] = _expand_dirs(config['USER_SERVICES'])
    log.info('Settings read from %s' % filename)

    update_settings(config=config)
    log.info('Settings updated from file %s' % filename)
    return True


@dispatcher.add_method
def save_settings(filename=None):
    """Save settings currently being used by DSL to a yaml file

    Parameters
    ----------

        filename : str
            path to yaml file in which to save settings

    Returns
    -------

        True
            Settings saved successfully

    Example
    -------
    >>> dsl.api.save_settings('/Users/dharhas/mydslsettings.yml')
    """
    if filename is None:
        filename = _default_config_file()

    with open(filename, 'w') as f:
        f.write(yaml.safe_dump(settings, default_flow_style=False))
        log.info('Settings written to %s' % filename)

    log.info('Settings written to %s' % filename)

    return True


def _default_config_file():
    base = get_settings()['BASE_DIR']
    return os.path.join(base, 'dsl_config.yml')


def _default_dsl_dir():
    dsl_dir = os.environ.get('ENVSIM_DSL_DIR')
    if dsl_dir is None:
        dsl_dir = appdirs.user_data_dir('dsl', 'envsim')

    return dsl_dir


def _expand_dirs(local_services):
    "if any dir ends in * then walk the subdirectories looking for dsl.yml"
    if local_services == []:
        return []

    expanded = []
    for path in local_services:
        head, tail = os.path.split(path)
        if tail == '*':
            for root, dirs, files in os.walk(head):
                if os.path.exists(os.path.join(root, 'dsl.yml')):
                    expanded.append(root)
        else:
            expanded.append(path)

    return expanded
