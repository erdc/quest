"""Python API for Environmental Simulator Data Services Library (DSL)

This module defines the Python API for the Environmental Simulator 
Data Services Library. 
"""

__version__ = 1.0

from ..util import (
        get_settings,
        save_settings, 
        update_settings, 
        update_settings_from_file,
    )

from .version import (
        get_dsl_version,
        get_api_version,
    )

from .collections import (
        get_collections,
        new_collection,
        update_collection,
        delete_collection,
    )

from .datasets import (
        download_dataset,
        download_dataset_options,
        update_dataset,
        describe_dataset,
        view_dataset,
    )

from .features import (
        add_to_collection,
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
        get_mapped_parameters,
        get_parameters,
        new_parameter,
        update_parameters,
        delete_parameters,   
    )


from .projects import (
       add_project,
       new_project,
       delete_project,
       get_projects,
       set_active_project,
   )


from .services import (
        get_providers,
        get_services,
        new_service,
        update_service,
        delete_service,
    )
