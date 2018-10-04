import os
import yaml
import logging

from ..database import get_db


log = logging.getLogger(__name__)

settings = {}


def get_settings():
    """Get the settings currently being used by QUEST.

    Returns:
        A dictionary of the current settings.

    Example:
        {'BASE_DIR': '/Users/dharhas/',
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
    """Update the settings file that is being stored in the Quest
       settings directory.

    Notes:
        Only key/value pairs that are provided are updated,
        any other existing pairs are left unchanged or defaults
        are used.

    Args:
        config (dict): Key/value pairs of settings that are to be updated.

    Returns:
        Updated Settings

    Example:
        {'BASE_DIR': '/Users/dharhas/',
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
    settings.setdefault('CACHE_DIR', os.path.join('.cache', 'user_cache'))
    settings.setdefault('PROJECTS_DIR', 'projects')
    settings.setdefault('USER_SERVICES', [])

    # reset connection to database in new PROJECT_DIR
    if 'BASE_DIR' in config.keys() or 'PROJECTS_DIR' in config.keys():
        get_db(reconnect=True)

    # reload providers
    if 'USER_SERVICES' in config.keys():
        from ..plugins.plugins import load_providers
        load_providers(update_cache=True)

    return settings


def update_settings_from_file(filename):
    """Update the settings from a new yaml file.

    Notes:
        Only key/value pairs that are provided are updated,
        any other existing pairs are left unchanged or defaults
        are used.

    Args:
        filename (string): Path to the yaml file containing the new settings.

    Returns:
        Updated settings

    Example:
        {'BASE_DIR': '/Users/dharhas/',
        'CACHE_DIR': 'cache',
        'PROJECTS_DIR': 'projects',
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
    """Save settings currently being used by QUEST to a yaml file.

    Args:
        filename (string): Path to the yaml file to save the settings.

    Returns:
        A true boolean if settings were saved successfully.

    """
    if filename is None:
        filename = _default_config_file()

    path = os.path.dirname(filename)
    if path:
        os.makedirs(path, exist_ok=True)

    with open(filename, 'w') as f:
        f.write(yaml.safe_dump(settings, default_flow_style=False))
        log.info('Settings written to %s' % filename)

    log.info('Settings written to %s' % filename)

    return True


def _default_config_file():
    """Gives the absolute path of where the settings directiory is.

    Returns:
        A string that is an absolute path to the settings directory.

    """
    base = get_settings()['BASE_DIR']
    return os.path.join(base, '.settings', 'quest_config.yml')


def _default_quest_dir():
    """Gives the locations of the Quest directory.

    Returns:
        A string that is an absolute path to the Quest directory.

    """
    quest_dir = os.environ.get('QUEST_DIR')
    if quest_dir is None:
        quest_dir = os.path.join(os.path.expanduser("~"), 'Quest')

    return quest_dir


def _expand_dirs(local_services):
    """Gives a list of paths that have a quest yaml file in them.

    Notes:
        If any dir ends in * then walk the subdirectories looking for quest.yml
    Args:
        local_services (list): A list of avaliable paths.

    Returns:
        A list of avaliable paths to the quest yaml file.

    """
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
