"""Python API for Environmental Simulator Data Services Library (DSL).

This module defines the Python API for the Environmental Simulator Data
Services Library.
"""

__version__ = 1.0

# __all__ needed for autodoc to work

__all__ = (
    'get_settings',
    'save_settings',
    'update_settings',
    'update_settings_from_file',
    'get_dsl_version',
    'get_api_version',
    'get_metadata',
    # 'update_metadata',
    'get_collections',
    'new_collection',
    'update_collection', # replace with update
    'delete_collection',
    # 'stage_for_download',
    'download',
    'download_options',
    # 'locate_dataset',
    # 'add_dataset_to_feature',
    'new_dataset',
    # 'update_dataset',
    'describe_dataset',
    'vizualize_dataset',
    'add_features',
    'get_features',
    'new_feature',
    # 'update_feature',
    'delete_feature',
    'get_filters',
    'apply_filter',
    'apply_filter_options',
    'get_mapped_parameters',
    'get_parameters',
    'new_parameter',
    'update_parameter',
    'delete_parameter',
    'add_project',
    'new_project',
    'delete_project',
    'get_projects',
    'get_active_project',
    'set_active_project',
    'get_providers',
    'get_services',
    'new_service',
    'update_service',
    'delete_service',
)

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
    download,
    download_options,
    new_dataset,
    # update_dataset,
    describe_dataset,
    vizualize_dataset,
)

from .features import (
    add_features,
    get_features,
    new_feature,
    # update_feature,
    delete_feature,
)

from .filters import (
    get_filters,
    apply_filter,
    apply_filter_options,
)

from .metadata import (
    get_metadata,
)

from .parameters import (
    get_mapped_parameters,
    get_parameters,
    new_parameter,
    update_parameter,
    delete_parameter,
)

from .projects import (
    add_project,
    new_project,
    delete_project,
    get_projects,
    get_active_project,
    set_active_project,
)


from .services import (
    get_providers,
    get_services,
    new_service,
    update_service,
    delete_service,
)
