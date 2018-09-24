import param

from .collections import get_collections, new_collection
from .datasets import stage_for_download, download_datasets, open_dataset
from .catalog import search_catalog, add_datasets
from .tools import run_tool
from ..database import get_db, db_session
from ..static import DatasetStatus


def get_data(
        service_uri,
        search_filters,
        download_options=None,
        collection_name='default',
        use_cache=True,
        max_catalog_entries=10,
        as_open_datasets=True,
):
    """
    Downloads data from source uri and adds to a quest collection.

    Args:
        service_uri:
        search_filters:
        download_options:
        collection_name:
        use_cache:
        max_catalog_entries:
        as_open_datasets:

    Returns:
         the quest dataset name, or an python data structure if open_dataset=True.
    """
    if collection_name not in get_collections():
        new_collection(collection_name)

    # download the features (i.e. locations) and metadata for the given web service
    # the first time this is run it will take longer since it downloads
    # and caches all metadata for the given service.
    catalog_entries = search_catalog(
        uris=service_uri,
        filters=search_filters,
    )

    # Ensure number of features is reasonable before downloading
    if len(catalog_entries) > max_catalog_entries:
        raise RuntimeError('The number of service features found was {} which exceeds the `max_features` of {}.'
                           .format(len(catalog_entries), max_catalog_entries))

    if isinstance(download_options, param.Parameterized):
        download_options = dict(download_options.get_param_values())

    datasets = list()
    cached_datasets = list()

    if use_cache:
        matched = _get_cached_data(catalog_entries, download_options, collection_name)
        catalog_entries = set(catalog_entries) - set(matched.keys())
        cached_datasets = list(matched.values())

    # add the selected features to a quest collection
    if catalog_entries:
        datasets = add_datasets(collection_name, list(catalog_entries))

        stage_for_download(uris=datasets, options=download_options)

        # download the staged datasets (if as_open_datasets is True then raise any errors)
        download_datasets(datasets=datasets, raise_on_error=as_open_datasets)

    datasets.extend(cached_datasets)

    if as_open_datasets:
        datasets = [open_dataset(dataset) for dataset in datasets]

    return datasets


def get_seamless_data(
        service_uri,
        bbox,
        search_filters=None,
        download_options=None,
        collection_name='default',
        use_cache=True,
        max_catalog_entries=10,
        as_open_dataset=True,
):
    """
    Downloads raster data from source uri and adds to a quest collection.

    If multiple raster tiles are retrieved for the given bounds it calls a quest
    tool to merge the tiles into a single raster.

    Args:
        service_uri:
        bbox:
        search_filters:
        download_options:
        collection_name:
        use_cache:
        max_catalog_entries:
        as_open_dataset:

    Returns:
        the quest dataset name.
    """
    if not _is_tile_service(service_uri):
        raise ValueError('The service {} does not support seamless data. '
                         'Only raster tile services are supported.'.format(service_uri))

    search_filters = search_filters or dict()
    search_filters.update(bbox=bbox)

    datasets = get_data(
        service_uri=service_uri,
        search_filters=search_filters,
        download_options=download_options,
        collection_name=collection_name,
        use_cache=use_cache,
        max_catalog_entries=max_catalog_entries,
        as_open_datasets=False,
    )

    tool_name = 'raster-merge'
    tool_options = {'bbox': bbox, 'datasets': datasets}
    merged_dataset = None
    if use_cache:
        merged_dataset = _get_cached_derived_data(tool_name, tool_options)
        if as_open_dataset and merged_dataset is not None:
            merged_dataset = [open_dataset(dataset) for dataset in merged_dataset] or None

    if merged_dataset is None:
        # merge and clip into a single raster tile
        merged_dataset = run_tool(
            name=tool_name,
            options=tool_options,
            as_open_datasets=as_open_dataset,
        )['datasets']

    # update_metadata(uris=merged_dataset, display_name=dataset_name)
    # delete the original individual tiles
    # delete(datasets)

    return merged_dataset[0]


def _get_cached_data(catalog_entries, download_options, collection=None):
    """Returns datasets that have been successfully downloaded
    where `feature` and `options` match `collection_features` and `download_options`.

    Args:
        collection_features:
        download_options:

    Returns:

    """

    db = get_db()
    with db_session:
        datasets = db.Dataset.select(lambda d: d.catalog_entry in catalog_entries and
                                     d.status == DatasetStatus.DOWNLOADED and
                                     d.options == download_options
                                     )
        # # the last part of the query is not working for some reason so instead:
        # datasets = [d for d in datasets if d.options == download_options]
        if collection is not None:
            datasets = [d for d in datasets if d.collection.name == collection]

    return {d.catalog_entry: d.name for d in datasets}


def _get_cached_derived_data(tool_name, tool_options):
    """

    Args:
        tool_name:
        tool_options:

    Returns:

    """
    options = {
        'tool_applied': tool_name,
        'tool_options': tool_options,
    }
    db = get_db()
    with db_session:
        datasets = db.Dataset.select(lambda d: d.options == options)

    return [d.name for d in datasets] or None


def _is_tile_service(service_uri):
    """

    Args:
        service_uri:

    Returns:

    """
    # TODO check to make sure the service provides raster tiles that can be merged.
    return True
