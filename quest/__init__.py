"""Quest
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data providers.
    Part of the Environmental Simulator project.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import pbr.version
import logging
from . import api  # NOQA: F401

logging.getLogger('ulmo').propagate = False

# set version number
__version__ = pbr.version.VersionInfo('quest').version_string_with_vcs()
