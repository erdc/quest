"""Module wide settings
"""
import appdirs
import logging
import os
import yaml

log = logging.getLogger(__name__)

settings = {}

def update_settings(config={}):
    print __name__
    config.setdefault('BASE_DIR', _default_dsl_dir())
    config.setdefault('CACHE_DIR', os.path.join(config['BASE_DIR'], 'cache'))
    config.setdefault('DATA_DIR', os.path.join(config['BASE_DIR'], 'data'))
    config.setdefault('CONFIG_FILE', os.path.join(config['BASE_DIR'], 'dsl_config.yml'))
    config.setdefault('COLLECTIONS_INDEX_FILE', os.path.join(config['BASE_DIR'], 'dsl_collections.yml'))
    config.setdefault('WEB_SERVICES', [])
    config.setdefault('LOCAL_SERVICES', [])

    settings = config


def update_settings_from_file(filename):
    config = yaml.safe_load(open(config_file, 'r'))

    #convert keys to uppercase
    if config is not None:
        for k,v in config.iteritems():
            if v is not None:
                config.__dict__[k.upper()] = v

    #recursively parse for local services
    local_services = config.get('LOCAL_SERVICES')
    if local_services is not None:
        config.LOCAL_SERVICES = _expand_dirs(local_services)
    
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