"""Python API for Environmental Simulator Quest (QUEST).

This module defines the Python API for the Environmental Simulator Data
Services Library.
"""

__version__ = '2.3'

# __all__ needed for autodoc to work

__all__ = (
    'add_features',
    'add_project',
    'add_provider',  # add custom url or local folder as a service
    'apply_filter',
    'get_filter_options',
    'authenticate_provider',
    'cancel_tasks',
    'copy',
    'delete',  # replaces delete_dataset, delete_collection, delete_feature
    'delete_project',
    'delete_provider',
    'download',
    'download_datasets',
    'get_download_options',
    'get_active_project',
    'get_api_version',
    'get_auth_status',
    'get_collections',
    'get_datasets',
    'get_features',
    'get_filters',
    'get_mapped_parameters',
    'get_metadata',
    'get_parameters',
    'get_pending_tasks',
    'get_projects',
    'get_providers',
    'get_publishers',
    'get_quest_version',
    'get_services',
    'get_settings',
    'get_tags',
    'get_task',
    'get_tasks',
    'move',
    'new_collection',
    'new_dataset',
    'new_feature',
    'new_parameter',
    'new_project',
    'open_dataset',
    'publish',
    'get_publish_options',
    'remove_project',
    'remove_tasks',
    'save_settings',
    'set_active_project',
    'stage_for_download',
    'unauthenticate_provider',
    'update_metadata',  # replaces update_collection, update_feature, update_dataset
    'update_settings',
    'update_settings_from_file',
    'visualize_dataset',
    'get_visualization_options',
)

from ..util import (
    get_settings,
    save_settings,
    update_settings,
    update_settings_from_file,
)

from .version import (
    get_quest_version,
    get_api_version,
)

from .collections import (
    get_collections,
    new_collection,
)

from .datasets import (
    download,
    publish,
    download_datasets,
    get_download_options,
    get_publish_options,
    get_datasets,
    new_dataset,
    open_dataset,
    stage_for_download,
    visualize_dataset,
    get_visualization_options,
)

from .manage import (
    delete,
    move,
    copy,
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
    get_filter_options,
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
    remove_project,
    set_active_project,
    active_db,
)

from .providers import (
    get_providers,
    get_publishers,
    get_services,
    add_provider,
    delete_provider,
    get_auth_status,
    authenticate_provider,
    unauthenticate_provider,
)

from .tasks import (
    get_pending_tasks,
    get_task,
    get_tasks,
    cancel_tasks,
    remove_tasks,
)
