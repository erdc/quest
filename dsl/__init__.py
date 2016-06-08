"""data services library
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data services.
    Part of the Environmental Simulator project.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from . import util, api
import pbr.version
import os

# set version number
__version__ = pbr.version.VersionInfo('dsl').version_string_with_vcs()
_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_pkg_data_path(filename=None):
    """Return path to dsl package data directory."""
    if filename is None:
        filename = ''

    return os.path.join(_ROOT, 'data', filename)
