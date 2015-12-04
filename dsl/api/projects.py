"""API functions related to Projects

"""
from jsonrpc import dispatcher
from .. import util
import os
import yaml


@dispatcher.add_method
def add_project():
    """Add a existing DSL project to the list of available projects

    This to add existing dsl projects to current session
    """
    pass

       
@dispatcher.add_method
def new_project():
    """Create a new DSL project and add it to list of available projects
    """
    pass


@dispatcher.add_method
def delete_project():
    """Delete project from list of available projects. DO WE NEED A SEPERATE 
    REMOVE_PROJECT? DO WE DELETE ALL DATA UNDER PROJECT?
    """
    pass


@dispatcher.add_method
def get_projects():
    """Get list of available projects
    """
    pass


@dispatcher.add_method
def set_active_project():
    """Set active DSL project
    """
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
        yaml.safe_dump(projects, f, default_flow_style=False)