"""Quest
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data providers.
    Part of the Environmental Simulator project.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import pbr.version
import warnings
import logging

warnings.filterwarnings("ignore", message="numpy.dtype size changed")

from . import api  # NOQA

logging.getLogger('ulmo').propagate = False

# set version number
__version__ = pbr.version.VersionInfo('quest').version_string_with_vcs()
