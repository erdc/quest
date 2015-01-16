"""Define Python API for DSL

This file defines the Python API for the Environmental Simulator Data Services Library
"""

__version__ = 1.0

from .filters import get_filters
from .providers import get_providers
from .services import *
from .collections import (
        new_collection,
        get_collection,
        add_to_collection,
        delete_collection,
        delete_from_collection,
        update_collection,
        list_collections,
    )

