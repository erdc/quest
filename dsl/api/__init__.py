"""Python API for Environmental Simulator Data Services Library (DSL)

This module defines the Python API for the Environmental Simulator 
Data Services Library. 
"""

__version__ = 1.0


from .collections import (
        get_collections,
        new_collection,
        update_collection,
        delete_collection,
    )

from .datasets import (
        stage_dataset,
        download_staged_dataset,
        download_dataset,
        update_dataset,
        describe_dataset,
        open_dataset,
        view_dataset,
    )

from .features import (
        get_features,
        new_feature,
        update_feature,
        delete_feature,
    )

from .filters import (
        get_filters, 
        apply_filter, 
        apply_filter_options,
    )

from .parameters import (
        get_parameters,
        new_parameter,
        update_parameters,
        delete_parameters,   
    )

from .services import (
        get_services,
        new_service,
        update_service,
        delete_service,
    )
