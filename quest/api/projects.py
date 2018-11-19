import os
import shutil

import pandas as pd

from ..util import logger, get_projects_dir, read_yaml, write_yaml
from ..database.database import db_session, get_db, init_db


PROJECT_DB_FILE = 'metadata.db'
PROJECT_INDEX_FILE = 'project_index.yml'


def active_db():
    """Get the active database.

    Returns:
         path (string):
            file path to active project database
    """
    dbpath = _get_project_db(get_active_project())
    return dbpath


def add_project(name, path, activate=True):
    """Add a existing QUEST project to the list of available projects

    Args:
        name (string, Required):
            name of project; existing name can be used or  project can be renamed
        path (string, Required):
            path to existing project
        activate (bool, Optional, Default=True):
            if True, the added project is set as the currently active project
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
        projects.update({name: {'folder': folder}})
        _write_projects(projects)
        project = _load_project(name)
    except Exception as e:
        projects.pop(name)
        _write_projects(projects)
        raise ValueError('Invalid Project Folder: %s' % path)

    if activate:
        set_active_project(name)
    return project


def new_project(name, display_name=None, description=None, metadata=None,
                folder=None, activate=True):
    """Create a new QUEST project and add it to list of available projects.

    Args:
        name (string, Required):
            name of newly created project
        display_name (string, Optional, Default=None):
            display name for project
        description (string, Optional, Default=None):
            description of project
        metadata (dict, Optional, Default=None):
            user defined metadata
        folder (string, Optional, Default=None):
            folder where all project data will be saved
        activate (bool, Optional, Default=True):
            if True, set newly created project as currently active project

    """
    name = name.lower()
    projects = _load_projects()
    if name in projects.keys():
        raise ValueError('Project %s exists, please use a unique name' % name)

    _new_project(
        name=name,
        display_name=display_name,
        description=description,
        metadata=metadata,
        folder=folder,
        projects=projects,
    )

    if activate:
        set_active_project(name)
    return _load_project(name)


def delete_project(name):
    """Delete a project.

    Deletes a project and all data in the project folder.

    Args:
        name (string, Required):
             name of a project

    Returns:
        projects (dict):
            all remaining projects and their respective folders
    """
    projects = _load_projects()

    if name not in list(projects.keys()):
        logger.error('Project not found')
        return list(projects.keys())

    folder = projects[name]['folder']
    if not os.path.isabs(folder):
        path = os.path.join(get_projects_dir(), folder)
    else:
        path = folder
    if os.path.exists(path):
        logger.info('deleting all data under path: %s', path)
        shutil.rmtree(path)

    return remove_project(name)


def get_active_project():
    """Get active project name.

    Returns:
        name (string):
            name of currently active project

    """
    path = _get_projects_index_file()
    contents = read_yaml(path)
    default_project = contents.get('active_project')
    if default_project is None:
        projects = contents.get('projects') or _create_default_project()
        default_project = list(projects.keys())[0]
        contents.update({
            'active_project': default_project,
            'projects': projects
        })
        write_yaml(path, contents)
    return default_project


def get_projects(expand=False, as_dataframe=False):
    """Get list of available projects.

    Args:
         expand (bool, Optional, Default=False):
            include collection details and format as dict
        as_dataframe (bool, Optional, Default=False):
            include collection details and format as pandas dataframe

    Returns:
        projects (list, dict, or pandas Dataframe,Default=list):
             all available projects


    """
    projects = {}
    if not expand and not as_dataframe:
        return list(_load_projects().keys())

    for name, project in _load_projects().items():
        path = project['folder']
        if not os.path.isabs(path):
            path = os.path.join(get_projects_dir(), path)

        data = _load_project(name)
        data.update({
            'name': name,
            'folder': path,
        })

        projects[name] = data

    if as_dataframe:
        projects = pd.DataFrame.from_dict(projects, orient='index')

    return projects


def remove_project(name):
    """Remove a project from the list of available projects.

    This does not delete the project folder or data, just removes it from the
    index of available projects.

    Args:
        name (string,Required):
            name of project

     Returns:
        projects (dict):
            all remaining projects and their respective folders


    """
    projects = _load_projects()

    if name not in list(projects.keys()):
        logger.error('Project not found')
        return list(projects.keys())

    logger.info('removing %s from projects' % name)
    del projects[name]
    _write_projects(projects)

    active = None
    if name == get_active_project():
        if 'default' in projects.keys():
            active = 'default'
        elif len(projects) > 0:
            active = list(projects.keys())[0]

        if active is None:
            logger.info('All projects have been removed. Re-adding "default" project.')
            projects = get_projects()
            active = 'default'

        logger.info('changing active project from {} to {}'.format(name, active))
        set_active_project(active)

    return projects


def set_active_project(name):
    """Set active QUEST project.

    Args:
        name (string, Required):
            name of a project

    Returns:
        project (string):
            name of project currently set as active

    """
    path = _get_projects_index_file()
    contents = read_yaml(path)
    if name not in contents['projects'].keys():
        raise ValueError('Project %s does not exist' % name)
    contents.update({'active_project': name})
    write_yaml(path, contents)
    get_db(active_db(), reconnect=True)  # change active database
    return name


def _new_project(name, display_name=None, description=None, metadata=None, folder=None, projects=None):

    projects = projects or dict()

    if display_name is None:
        display_name = name

    if description is None:
        description = ''

    if folder is None:
        folder = name

    if metadata is None:
        metadata = {}

    if not os.path.isabs(folder):
        path = os.path.join(get_projects_dir(), folder)
    else:
        path = folder

    os.makedirs(path, exist_ok=True)
    dbpath = os.path.join(path, PROJECT_DB_FILE)
    if os.path.exists(dbpath):
        raise ValueError('Project database {} already exists, '
                         'please remove the database or use a different project folder.'.format(dbpath))
    db = init_db(dbpath)
    with db_session:
        db.Project(display_name=display_name,
                   description=description,
                   metadata=metadata)
    db.disconnect()
    projects.update({name: {'folder': folder}})
    _write_projects(projects)

    return projects


def _create_default_project():
    # create a default project if needed
    return _new_project('default', 'Default Project', 'Created by QUEST')


def _load_project(name):
    db = init_db(_get_project_db(name))
    with db_session:
        project = db.Project.get().to_dict()

    db.disconnect()
    del project['id']
    return project


def _load_projects():
    """load list of collections."""
    path = _get_projects_index_file()
    projects = read_yaml(path).get('projects')
    if not projects:
        projects = _create_default_project()

    return projects


def _write_projects(projects):
    """write list of collections to file."""
    path = _get_projects_index_file()
    contents = read_yaml(path)
    contents.update({'projects': projects})
    write_yaml(path, contents)


def _get_project_dir():
    return get_projects(expand=True)[get_active_project()]['folder']


def _get_project_db(name):
    projects = _load_projects()
    if name not in projects.keys():
        raise ValueError('Project %s not found' % name)

    path = projects[name]['folder']
    if not os.path.isabs(path):
        path = os.path.join(get_projects_dir(), path)

    return os.path.join(path, PROJECT_DB_FILE)


def _get_projects_index_file():
    return os.path.join(get_projects_dir(), PROJECT_INDEX_FILE)
