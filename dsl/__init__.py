"""
    data services library
    ~~~~~~~~~~~~~~~~~~~~~

    A library for environmental data services. Part of the Environmental Simulator project.
"""
from __future__ import absolute_import

from .version import __version__

from .init import init

from . import util, api

init()
