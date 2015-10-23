"""API functions related to Projects

"""
from jsonrpc import dispatcher
from .. import util
import os
import yaml

@dispatcher.add_method
def add_project:
    pass
       
@dispatcher.add_method
def new_project:
    pass

@dispatcher.add_method
def delete_project:
    pass

@dispatcher.add_method
def get_projects:
    pass

@dispatcher.add_method
def set_active_project:
    pass


def _read_projects_index():
    """load list of collections

    """
    path = util.get_projects_index()

    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return yaml.safe_load(f)


def _write_projects_index(projects):
    """write list of collections to  file 
    """
    path = util.get_projects_index()
    with open(path, 'w') as f:
        yaml.dump(projects, f, default_flow_style=False)