"""Quest
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data providers.
    Part of the Environmental Simulator project.
"""
import pbr.version
import warnings
import logging

logging.getLogger('ulmo').propagate = False
warnings.filterwarnings("ignore", message="numpy.dtype size changed")

from . import api  # NOQA
from . import tools  # NOQA

# set version number
__version__ = pbr.version.VersionInfo('quest').version_string_with_vcs()
