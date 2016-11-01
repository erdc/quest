"""data services library
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data services.
    Part of the Environmental Simulator project.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import pbr.version
import os

# set version number
__version__ = pbr.version.VersionInfo('dsl').version_string_with_vcs()
_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_pkg_data_path(*args):
    """Return path to dsl package data directory.

    *args: optional tuple to join with the pkg data path
    """
    return os.path.join(_ROOT, 'data', *args)


from . import util, api

# ensure at least one project exists
# create a default project if needed
if not api.get_projects():
    api.new_project('default', 'Default Project', 'Created by DSL')
    api.set_active_project('default')

# init active project db
#api.connect(api.active_db())
