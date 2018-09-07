"""Quest
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data providers.
    Part of the Environmental Simulator project.
"""
import pbr.version
import warnings
import logging
from . import tools

warnings.filterwarnings("ignore", message="numpy.dtype size changed")

from . import api  # NOQA


logging.getLogger('ulmo').propagate = False

# set version number
__version__ = pbr.version.VersionInfo('quest').version_string_with_vcs()
