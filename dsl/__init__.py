"""
    data services library
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data services. Part of the Environmental Simulator project.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from . import util, api
import pbr.version

# set version number
__version__ = pbr.version.VersionInfo('dsl').version_string_with_vcs()