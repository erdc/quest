"""API functions related to Projects."""
import datetime
from jsonrpc import dispatcher
import os
import shutil
from .. import util
from . import db

PROJECT_DB_FILE = 'metadata.db'
PROJECT_INDEX_FILE = 'project_index.yml'


def active_db():
    """Return path to active project database
    """
    return _get_project_db(get_active_project())

@dispatcher.add_method
def add_project(name, path):
    """Add a existing DSL project to the list of available projects.

    This to add existing dsl projects to current session
    """
    name = name.lower()
    projects = _load_projects()
    if name in projects.keys():
        raise ValueError('Project %s exists, please use a unique name' % name)
    if not os.path.exists(path):
        raise ValueError('Path does not exist: %s' % path)

    try:
        folder = path
        # new_projects = dict(projects)
        projects.update({name: {'_folder': folder}})
        _write_projects(projects)
        project = _load_project(name)
    except Exception as e:
        projects.pop(name)
        # print(projects)
        _write_projects(projects)
        raise ValueError('Invalid Project Folder: %s' % path)

    return project


@dispatcher.add_method
def new_project(name, display_name=None, description=None, metadata=None,
                folder=None):
    """Create a new DSL project and add it to list of available projects."""
    name = name.lower()
    projects = _load_projects()
    if name in projects.keys():
        raise ValueError('Project %s exists, please use a unique name' % name)

    if display_name is None:
        display_name = name

    if description is None:
        description = ''

    if folder is None:
        folder = name

    if metadata is None:
        metadata = {}

    if not os.path.isabs(folder):
        path = os.path.join(util.get_projects_dir(), folder)
    else:
        path = folder

    dsl_metadata = {
        'type': 'project',
        'display_name': display_name,
        'description': description,
        'created_on': datetime.datetime.now().isoformat(),
    }

    util.mkdir_if_doesnt_exist(path)
    dbpath = os.path.join(path, PROJECT_DB_FILE)
    _write_project(dbpath, dsl_metadata, metadata)
    projects.update({name: {'_folder': folder}})
    _write_projects(projects)

    return _load_project(name)


@dispatcher.add_method
def delete_project(name, delete_data=False):
    """delete a project.

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

    if name not in list(projects.keys()):
        print('Project not found')
        return projects

    if delete_data:
        folder = projects[name]['_folder']
        if not os.path.isabs(folder):
            path = os.path.join(util.get_projects_dir(), folder)
        else:
            path = folder
        if os.path.exists(path):
            print('deleting all data under path:', path)
            shutil.rmtree(path)

    print('removing %s from projects' % name)
    del projects[name]
    _write_projects(projects)
    return projects


@dispatcher.add_method
def get_active_project():
    """Get active project name."""
    path = _get_projects_index_file()
    return util.read_yaml(path).get('active_project', 'default')


@dispatcher.add_method
def get_projects(metadata=None):
    """Get list of available projects."""
    projects = {}
    if not metadata:
        return list(_load_projects().keys())

    for name, project in _load_projects().items():
        path = project['_folder']
        if not os.path.isabs(path):
            path = os.path.join(util.get_projects_dir(), path)

        data = _load_project(name)
        data.update({
            '_name': name,
            '_folder': path,
        })

        projects[name] = util.to_metadata(data)

    return projects


@dispatcher.add_method
def set_active_project(name):
    """Set active DSL project."""
    path = _get_projects_index_file()
    contents = util.read_yaml(path)
    if name not in contents['projects'].keys():
        raise ValueError('Project %s does not exist' % name)
    contents.update({'active_project': name})
    util.write_yaml(path, contents)
    return name


def _load_project(name):
    dbpath = _get_project_db(name)
    return db.read_data(dbpath, 'project', 'project_metadata')


def _load_projects():
    """load list of collections."""
    path = _get_projects_index_file()
    projects = util.read_yaml(path).get('projects')
    # make sure a default project exists
    default_dir = os.path.join(util.get_projects_dir(), 'default_project')
    dbpath = os.path.join(default_dir, PROJECT_DB_FILE)
    if projects is None or not os.path.exists(dbpath):
        projects = projects or {}
        projects['default'] = {'_folder': 'default_project'}
        util.mkdir_if_doesnt_exist(default_dir)
        dsl_metadata = {
            'type': 'project',
            'display_name': 'Default Project',
            'description': 'Created by DSL',
            'created_on': datetime.datetime.now().isoformat(),
        }
        util.mkdir_if_doesnt_exist(default_dir)
        _write_project(dbpath, dsl_metadata)
        _write_projects(projects)
        set_active_project('default')

    return projects


def _write_project(dbpath, dsl_metadata, metadata=None):
    db.upsert(dbpath, 'project', 'project_metadata', dsl_metadata, metadata)


def _write_projects(projects):
    """write list of collections to file."""
    path = _get_projects_index_file()
    contents = util.read_yaml(path)
    contents.update({'projects': projects})
    util.write_yaml(path, contents)


def _get_project_db(name):
    projects = _load_projects()
    if name not in projects.keys():
        raise ValueError('Project %s not found' % name)

    path = projects[name]['_folder']
    if not os.path.isabs(path):
        path = os.path.join(util.get_projects_dir(), path)

    util.mkdir_if_doesnt_exist(path)
    return os.path.join(path, PROJECT_DB_FILE)


def _get_projects_index_file():
    return os.path.join(util.get_projects_dir(), PROJECT_INDEX_FILE)
