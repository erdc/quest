"""Module wide settings.

"""

import appdirs
import logging
import os
import yaml

from ..database import get_db

log = logging.getLogger(__name__)

settings = {}


def get_settings():
    """Get the settings currently being used by QUEST.

    Returns
    -------
        settings : dict
            Dictionary of current settings

    Example
    -------
    >>> quest.api.get_settings()
    {'BASE_DIR': '/Users/dharhas/Library/Application Support/quest',
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


def update_settings(config={}):
    """Update settings currently being used by QUEST

    Only key/value pairs that are provided are updated,
    any other existing pairs are left unchanged or defaults
    are used.

    Parameters
    ----------
        config : dict
            key/value pairs of settings that are to be updated.

    Returns
    -------
        Updated Settings

    Example
    -------
    >>> quest.api.update_settings({'BASE_DIR':'/Users/dharhas/myquestdir'})
    {'BASE_DIR': '/Users/dharhas/myquestdir',
     'CACHE_DIR': 'cache',
     'PROJECTS_DIR': 'projects',
     'USER_SERVICES': [],
     }
    """

    global settings
    if 'BASE_DIR' in config.keys() and not os.path.isabs(config['BASE_DIR']):
        config['BASE_DIR'] = os.path.join(os.getcwd(), config['BASE_DIR'])
    settings.update(config)
    settings.setdefault('BASE_DIR', _default_quest_dir())
    settings.setdefault('CACHE_DIR', 'cache')
    settings.setdefault('PROJECTS_DIR', 'projects')
    settings.setdefault('USER_SERVICES', [])

    # reset connection to database in new PROJECT_DIR
    if 'BASE_DIR' in config.keys() or 'PROJECTS_DIR' in config.keys():
        get_db(reconnect=True)

    return settings


def update_settings_from_file(filename):
    """Update settings currently being used by QUEST from a yaml file

    Only key/value pairs that are provided are updated,
    any other existing pairs are left unchanged or defaults
    are used.

    Parameters
    ----------
        filename : str
            path to yaml file containing settings

    Returns
    -------
        Updated settings

    Example
    -------
    >>> quest.api.update_settings_from_file('/Users/dharhas/myquestsettings.yml')
    {'BASE_DIR': '/Users/dharhas/myquest2dir',
     'CACHE_DIR': 'cache',
     'PROJECTS_DIR': 'data',
     'USER_SERVICES': [],
     }
    """
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)

    # convert keys to uppercase
    config = dict((k.upper(), v) for k, v in config.items())

    # recursively parse for local providers
    config['USER_SERVICES'] = _expand_dirs(config['USER_SERVICES'])
    log.info('Settings read from %s' % filename)

    update_settings(config=config)
    log.info('Settings updated from file %s' % filename)
    return settings


def save_settings(filename=None):
    """Save settings currently being used by QUEST to a yaml file

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
    >>> quest.api.save_settings('/Users/dharhas/myquestsettings.yml')
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
    return os.path.join(base, 'quest_config.yml')


def _default_quest_dir():
    quest_dir = os.environ.get('QUEST_DIR')
    if quest_dir is None:
        quest_dir = appdirs.user_data_dir('quest', 'erdc')

    return quest_dir


def _expand_dirs(local_services):
    "if any dir ends in * then walk the subdirectories looking for quest.yml"
    if local_services == []:
        return []

    expanded = []
    for path in local_services:
        head, tail = os.path.split(path)
        if tail == '*':
            for root, dirs, files in os.walk(head):
                if os.path.exists(os.path.join(root, 'quest.yml')):
                    expanded.append(root)
        else:
            expanded.append(path)

    return expanded
