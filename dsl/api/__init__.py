"""Python API for Environmental Simulator Data Services Library (DSL).

This module defines the Python API for the Environmental Simulator Data
Services Library.
"""

__version__ = '2.0beta'

# __all__ needed for autodoc to work

__all__ = (
    'get_settings',
    'save_settings',
    'update_settings',
    'update_settings_from_file',
    'get_dsl_version',
    'get_api_version',
    'get_metadata',
    'update_metadata', # replaces update_collection, update_feature, update_dataset
    'delete', # replaces delete_dataset, delete_collection, delete_feature
    'get_collections',
    'new_collection',
    'stage_for_download',
    'download',
    'download_datasets',
    'download_options',
    'get_datasets',
    'new_dataset',
    'open_dataset',
    'visualize_dataset',
    'visualize_dataset_options',
    'add_features',
    'get_features',
    'get_tags',
    'new_feature',
    'get_filters',
    'apply_filter',
    # 'apply_filter_set', # apply a list of filters
    'apply_filter_options',
    'get_mapped_parameters',
    'get_parameters',
    'new_parameter',
    # 'update_parameter',
    # 'delete_parameter',
    'add_project',
    'new_project',
    'delete_project',
    'get_projects',
    'get_active_project',
    'set_active_project',
    'get_providers',
    'get_services',
    'add_provider',  # add custom url or local folder as a service
    'delete_provider',
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
)

from .datasets import (
    download,
    download_datasets,
    download_options,
    get_datasets,
    new_dataset,
    open_dataset,
    stage_for_download,
    visualize_dataset,
    visualize_dataset_options,
)

from .delete import (
    delete,
)

from .features import (
    add_features,
    get_features,
    get_tags,
    new_feature,
)

from .filters import (
    get_filters,
    apply_filter,
    # apply_filter_set
    apply_filter_options,
)

from .metadata import (
    get_metadata,
    update_metadata,
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
    active_db,
)

from .database import get_db

from .services import (
    get_providers,
    get_services,
    add_provider,
    delete_provider,
)
