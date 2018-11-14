import param

from .collections import get_collections, new_collection
from .datasets import stage_for_download, download_datasets, open_dataset
from .catalog import search_catalog, add_datasets
from .tools import run_tool
from ..database import get_db, db_session
from ..util import logger as log
from ..static import DatasetStatus, UriType


def get_data(
        service_uri,
        search_filters,
        download_options=None,
        collection_name='default',
        use_cache=True,
        max_catalog_entries=10,
        as_open_datasets=True,
        raise_on_error=False,
):
    """
    Downloads data from source uri and adds to a quest collection.

    Args:
        service_uri (string, required):
            uri for service to get data from
        search_filters (dict, required):
            dictionary of search filters to filter the catalog search (see docs for quest.api.search_catalog)
        download_options (dict or Parameterized, optional, default=None):
            dictionary or Parameterized object with download options for service
            (see docs for quest.api.download_datasets)
        collection_name (string, optional, default='default'):
            name of collection to add downloaded data to. If collection doesn't exist it will be created.
        use_cache (bool, optional, default=True):
            if True then previously downloaded datasets with the same download options will be returned
            rather than downloading new datasets
        max_catalog_entries (int, optional, default=10):
            the maximum number of datasets to allow in the search. If exceeded a Runtime error is raised.
        as_open_datasets (bool, optional, default=False):
            if True return datasets as Python data structures rather than as dataset ids
            (see docs for quest.api.open_dataset)
        raise_on_error (bool, optional, default=False):
            if True then raise an exception if no datasets are returned in the search,
            or if there is an error while downloading any of the datasets.

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

    if not catalog_entries:
        log.warn('Search was empty. No datasets will be downloaded.')
        if raise_on_error:
            raise RuntimeError('Search was empty. No datasets will be downloaded.')

    # Ensure number of features is reasonable before downloading
    if len(catalog_entries) > max_catalog_entries:
        raise RuntimeError('The number of service features found was {} which exceeds the `max_features` of {}.'
                           .format(len(catalog_entries), max_catalog_entries))

    if isinstance(download_options, param.Parameterized):
        download_options = dict(download_options.get_param_values())

    datasets = list()
    cached_datasets = list()
    num_entries = len(catalog_entries)

    if use_cache:
        matched = _get_cached_data(catalog_entries, download_options, collection_name)
        catalog_entries = set(catalog_entries) - set(matched.keys())
        cached_datasets = list(matched.values())

    # add the selected features to a quest collection
    if catalog_entries:
        datasets = add_datasets(collection_name, list(catalog_entries))

        stage_for_download(uris=datasets, options=download_options)

        # download the staged datasets
        for dataset in datasets:
            try:
                download_datasets(datasets=dataset, raise_on_error=True)
            except Exception as e:
                log.exception('The following error was raised while downloading dataset {}'.format(dataset), exc_info=e)
                if raise_on_error:
                    raise e

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
        raise_on_error=False,

):
    """
    Downloads raster data from source uri and adds to a quest collection.

    If multiple raster tiles are retrieved for the given bounds it calls a quest
    tool to merge the tiles into a single raster.

    Args:
        service_uri (string, required):
            uri for service to get data from
        bbox (list, required):
            list of lat/lon coordinates representing the bounds of the data in for form
            [lon_min, lat_min, lon_max, lat_max].
        search_filters (dict, required):
            dictionary of search filters to filter the catalog search (see docs for quest.api.search_catalog)
        download_options (dict or Parameterized, optional, default=None):
            dictionary or Parameterized object with download options for service
            (see docs for quest.api.download_datasets)
        collection_name (string, optional, default='default'):
            name of collection to add downloaded data to. If collection doesn't exist it will be created.
        use_cache (bool, optional, default=True):
            if True then previously downloaded datasets with the same download options will be returned
            rather than downloading new datasets
        max_catalog_entries (int, optional, default=10):
            the maximum number of datasets to allow in the search. If exceeded a Runtime error is raised.
        as_open_dataset (bool, optional, default=False):
            if True return dataset as Python data structure rather than as a dataset id
            (see docs for quest.api.open_dataset)
        raise_on_error (bool, optional, default=False):
            if True then raise an exception if no datasets are returned in the search,
            or if there is an error while downloading.

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
        raise_on_error=raise_on_error,
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
    where `catalog_entry` and `options` match `catalog_entries` and `download_options`.

    Args:
        catalog_entries (list, required):
            list of catalog_entry ids to check for matching downloaded data
        download_options (dict, required):
            dictionary of download options to match against previously downloaded data
        collection (string, optional, default=None):
            Optionally only match cached data from within given collection.

    Returns:
        a dictionary of dataset ids mapped to provided catalog entries
    """

    db = get_db()
    with db_session:
        datasets = db.Dataset.select(lambda d: d.catalog_entry in catalog_entries and
                                     d.status == DatasetStatus.DOWNLOADED and
                                     d.options == download_options
                                     )
        if collection is not None:
            datasets = [d for d in datasets if d.collection.name == collection]

    return {d.catalog_entry: d.name for d in datasets}


def _get_cached_derived_data(tool_name, tool_options):
    """Returns datasets that have been generated by Quest tools where `tool_applied` and `tool_options`
     match the arguments `tool_name` and `tool_options`.

    Args:
        tool_name (string, required):
            name of quest tool that was run to generate data
        tool_options (dict, required):
            dictionary of tool options used to generate data

    Returns:
        a list of dataset ids that have matached arguments or None

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
    """Checks that `service_uri` is a data service that provides tiled raster data.

    Args:
        service_uri (string, required):
            string of a service to verify that it provides tiles

    Returns:
        True if service provides tiles, False otherwise
    """
    # TODO check to make sure the service provides raster tiles that can be merged.
    return True
