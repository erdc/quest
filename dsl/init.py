import appdirs
from . import settings
import os
import yaml


def init(config_file=None):
    """Setup DSL directories, web and local services
    """
    import sys
    sys.argv = ()

    if config_file is None:
        dsl_dir = os.environ.get('ENVSIM_DSL_DIR')
        if dsl_dir is None:
            dsl_dir = appdirs.user_data_dir('data-services-library', 'envsim')
        settings.DSL_DIR = dsl_dir
        config_file = os.path.join(dsl_dir, settings.DSL_CONFIG)

    if os.path.isfile(config_file):
        _load_dsl_config(config_file)


def _load_dsl_config(config_file):
    config = yaml.load(open(config_file, 'r'))

    #read in dsl settings, settings are always upper case 
    custom_settings = config.get('settings')
    if settings is not None:
        for k,v in custom_settings.iteritems():
            if v is not None:
                settings.__dict__[k.upper()] = v

    if settings.DSL_DIR is None:
        settings.DSL_DIR = os.path.os.path.dirname(config_file)

    web_services = config.get('web_services')
    if web_services is not None:
        settings.WEB_SERVICES = web_services

    local_services = config.get('local_services')
    if local_services is not None:
        settings.LOCAL_SERVICES = _expand_dirs(local_services)


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
