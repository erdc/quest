"""API functions related to Projects

"""
import datetime
from jsonrpc import dispatcher
import os
import shutil
from .. import util


@dispatcher.add_method
def add_project(uid, path):
    """Add a existing DSL project to the list of available projects

    This to add existing dsl projects to current session
    """
    uid = uid.lower()
    projects = _load_projects()
    if uid in projects.keys():
        raise ValueError('Project %s exists, please use a unique name' % uid)

    try:
        project = util.read_yaml(os.path.join(path, 'dsl.yml'))
    except:
        raise ValueError('Invalid Project Folder: %s' % path)

    folder = path
    projects.update({uid: {'folder': folder}})
    _write_projects(projects)
    return project


@dispatcher.add_method
def new_project(uid, metadata={}, folder=None):
    """Create a new DSL project and add it to list of available projects
    """
    uid = uid.lower()
    projects = _load_projects()
    if uid in projects.keys():
        raise ValueError('Project %s exists, please use a unique name' % uid)

    if folder is None:
        folder = uid

    if not os.path.isabs(folder):
        path = os.path.join(util.get_projects_dir(), folder)
    else:
        path = folder

    metadata.update({
        'display_name': metadata.get('display_name', uid),
        'description': metadata.get('description', None),
        'created_on': datetime.datetime.now().isoformat(),
    })
    project = {'metadata': metadata}

    util.mkdir_if_doesnt_exist(path)
    util.write_yaml(os.path.join(path, 'dsl.yml'), project)
    projects.update({uid: {'folder': folder}})
    _write_projects(projects)

    return project


@dispatcher.add_method
def delete_project(uid, delete_data=False):
    """delete a project

    Deletes a collection from the collections metadata file.
    Optionally deletes all data under collection.

    Parameters
    ----------
        name : str,
            The name of the collection

        delete_data : bool,
            if True all data in the collection will be deleted

        Returns
        -------
        projects : dict,
            A python dict representation of the list of available collections,
            the updated collections list is also written to a json file.
    """
    projects = _load_projects()

    if uid not in list(projects.keys()):
        print('Project not found')
        return projects

    if delete_data:
        folder = projects[uid]['folder']
        if not os.path.isabs(folder):
            path = os.path.join(util.get_projects_dir(), folder)
        else:
            path = folder
        if os.path.exists(path):
            print('deleting all data under path:', path)
            shutil.rmtree(path)

    print('removing %s from projects' % uid)
    del projects[uid]
    _write_projects(projects)
    return projects


@dispatcher.add_method
def get_active_project():
    """Get active project uid
    """
    path = _get_projects_index_file()
    return util.read_yaml(path).get('active_project')


@dispatcher.add_method
def get_projects():
    """Get list of available projects
    """
    return _load_projects()


@dispatcher.add_method
def set_active_project(uid):
    """Set active DSL project
    """
    path = _get_projects_index_file()
    contents = util.read_yaml(path)
    if uid not in contents['projects'].keys():
        raise ValueError('Project %s does not exist' % uid)
    contents.update({'active_project': uid})
    util.write_yaml(path, contents)
    return uid


def _load_projects():
    """load list of collections

    """
    path = _get_projects_index_file()
    projects = util.read_yaml(path).get('projects')
    # make sure a default project exists
    if projects is None:
        print('INSIDE LOOP')
        projects = {
            'default': {'folder': 'default_project'}
        }
        default_dir = os.path.join(util.get_projects_dir(), 'default_project')
        util.mkdir_if_doesnt_exist(default_dir)
        _write_projects(projects)

    return projects


def _write_project(uid, project):
    """write collection

    """
    util.write_yaml(_get_project_file(uid), project)


def _write_projects(projects):
    """write list of collections to file
    """
    path = _get_projects_index_file()
    contents = util.read_yaml(path)
    contents.update({'projects': projects})
    util.write_yaml(path, contents)


def _get_project_file(uid):
    projects = _load_projects()
    if uid not in projects.keys():
        raise ValueError('Project %s not found' % uid)

    path = projects[uid]['folder']
    if not os.path.isabs(path):
        path = os.path.join(util.get_projects_dir(), path)

    util.mkdir_if_doesnt_exist(path)
    return os.path.join(path, 'dsl.yml')


def _get_projects_index_file():
    return os.path.join(util.get_projects_dir(), 'dsl.yml')
