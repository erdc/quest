"""Module wide settings
"""
from __future__ import print_function
import appdirs
import logging
import os
import yaml

log = logging.getLogger(__name__)

settings = {}


def get_settings():
    global settings
    if not settings:
        update_settings()

    return settings


def update_settings(config={}):
    global settings
    config.setdefault('BASE_DIR', _default_dsl_dir())
    config.setdefault('CACHE_DIR', 'cache')
    config.setdefault('DATA_DIR', 'data')
    config.setdefault('CONFIG_FILE', 'dsl_config.yml')
    config.setdefault('COLLECTIONS_INDEX_FILE', 'dsl_collections.yml')
    config.setdefault('WEB_SERVICES', [])
    config.setdefault('LOCAL_SERVICES', [])

    settings.update(config)


def update_settings_from_file(filename):
    config = yaml.safe_load(open(filename, 'r'))

    #convert keys to uppercase
    config = dict((k.upper(), v) for k, v in config.items())
    print(config)

    #recursively parse for local services
    config['LOCAL_SERVICES'] = _expand_dirs(config['LOCAL_SERVICES'])
    log.info('Settings read from %s' % filename)

    update_settings(config=config)


def save_settings(filename):
    with open(filename, 'w') as f:
        f.write(yaml.dump(settings, default_flow_style=False))
        log.info('Settings written to %s' % filename)
    

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
        if tail=='*':
            for root, dirs, files in os.walk(head):
                if os.path.exists(os.path.join(root, 'dsl.yml')):
                    expanded.append(root)
        else:
            expanded.append(path)

    return expanded