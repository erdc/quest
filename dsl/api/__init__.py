"""Python API for Environmental Simulator Data Services Library (DSL)

This module defines the Python API for the Environmental Simulator 
Data Services Library. 


Nomenclature:

Services
Filters
Readers






"""

__version__ = 1.0

from .filters import get_filters
from .providers import get_providers
from .services import (
        get_data,
        get_locations,
        get_parameters,
        get_services,
    )
from .collections import (
        new_collection,
        get_collection,
        add_to_collection,
        delete_collection,
        delete_from_collection,
        download_in_collection,
        update_collection,
        list_collections,
    )

