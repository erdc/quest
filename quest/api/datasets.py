import os

import param
import pandas as pd

from .tasks import add_async
from .projects import _get_project_dir
from .collections import get_collections
from .metadata import get_metadata, update_metadata
from .. import util
from .. import static
from ..plugins import load_providers, load_plugins, list_plugins
from ..database.database import get_db, db_session, select_datasets


@add_async
def download(catalog_entry, file_path, dataset=None, **kwargs):
    """Download dataset and save it locally.

    Args:
        catalog_entry (string, Required):
            uri of catalog_entry within a service or collection
        file_path (string, Required):
            path location to save downloaded data
        dataset (string, Optional, Default=None):
            maybe only be used by some providers
        async: (bool, Optional, Default=False)
            if True, download in background
        kwargs:
            optional download kwargs

    Returns:
        data (dict):
            details of downloaded data

    """
    service_uri = catalog_entry

    if file_path is None:
        pass

    provider, service, catalog_id = util.parse_service_uri(service_uri)
    provider_plugin = load_providers()[provider]
    data = provider_plugin.download(service=service, catalog_id=catalog_id,
                                    file_path=file_path, dataset=dataset, **kwargs)
    return data


@add_async
def publish(publisher_uri, options=None, **kwargs):
    if isinstance(options, param.Parameterized):
        options = dict(options.get_param_values())
    options = options or dict()
    options.update(kwargs)
    provider, publisher, _ = util.parse_service_uri(publisher_uri)
    provider_plugin = load_providers()[provider]
    data = provider_plugin.publish(publisher=publisher, **options)
    return data

@add_async
def download_datasets(datasets, raise_on_error=False):
    """Download datasets that have been staged with stage_for_download.

    Args:
        datasets (string or list, Required):
            datasets to download
        raise_on_error (bool, Optional, Default=False):
            if True, if an error occurs raise an exception
        async: (bool, Optional, Default=False)
            if True, download in background

    Returns:
        status (dict):
            download status of datasets
    """
    datasets = get_metadata(datasets, as_dataframe=True)

    if datasets.empty:
        return

    # filter out non download datasets
    datasets = datasets[datasets['source'] == static.DatasetSource.WEB_SERVICE]

    db = get_db()
    project_path = _get_project_dir()
    status = {}
    for idx, dataset in datasets.iterrows():
        collection_path = os.path.join(project_path, dataset['collection'])
        catalog_entry = dataset["catalog_entry"]
        try:
            update_metadata(idx, quest_metadata={'status': static.DatasetStatus.PENDING})
            kwargs = dataset['options'] or dict()
            all_metadata = download(catalog_entry,
                                    file_path=collection_path,
                                    dataset=idx, **kwargs)

            metadata = all_metadata.pop('metadata', None)
            quest_metadata = all_metadata
            quest_metadata.update({
                'status': static.DatasetStatus.DOWNLOADED,
                'message': 'success',
                })
        except Exception as e:
            if raise_on_error:
                raise

            quest_metadata = {
                'status': static.DatasetStatus.FAILED_DOWNLOAD,
                'message': str(e),
                }

            metadata = None

        status[idx] = quest_metadata['status']

        quest_metadata.update({'metadata': metadata})

        with db_session:
            dataset = db.Dataset[idx]
            dataset.set(**quest_metadata)

    return status


def get_download_options(uris, fmt='json'):
    """List optional kwargs that can be specified when downloading a dataset.

   Args:
        uris (string or list, Required):
            uris of catalog_entries or datasets
        fmt (string, Required, Default='json'):
            format in which to return download_options. One of ['json', 'param']


    Returns:
        download_options (dict):
            download options that can be specified when calling
            quest.api.stage_for_download or quest.api.download
    """
    uris = util.listify(uris)
    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=['collections'])

    services = grouped_uris.get(static.UriType.SERVICE) or []
    datasets = grouped_uris.get(static.UriType.DATASET) or []

    service_uris = {s: s for s in services}
    service_uris.update({dataset: get_metadata(dataset)[dataset]['catalog_entry'] for dataset in datasets})

    options = {}
    for uri, service_uri in service_uris.items():
        provider, service, _ = util.parse_service_uri(service_uri)
        provider_plugin = load_providers()[provider]
        options[uri] = provider_plugin.get_download_options(service, fmt)

    return options


def get_publish_options(publish_uri, fmt='json'):
    uris = util.listify(publish_uri)
    options = {}
    for uri in uris:
        publish_uri = uri
        provider, publisher, _ = util.parse_service_uri(publish_uri)
        provider_plugin = load_providers()[provider]
        options[uri] = provider_plugin.publish_options(publisher, fmt)

    return options


@add_async
def get_datasets(expand=None, filters=None, queries=None, as_dataframe=None):
    """Return all available datasets in active project.

    Args:
        expand (bool, Optional, Default=None):
            include dataset details and format as dict
        filters(dict, Optional, Default=None):
             filter dataset by any metadata field
        queries(list, Optional, Default=None):
            list of string arguments to pass to pandas.DataFrame.query to filter the datasets
        as_dataframe (bool or None, Optional, Default=None):
            include dataset details and format as pandas dataframe
    Returns:
        uris (list, dict, pandas Dataframe, Default=list):
            staged dataset uids

    """
    datasets = select_datasets()
    datasets = pd.DataFrame(datasets)
    if not datasets.empty:
        datasets.set_index('name', inplace=True, drop=False)

    if datasets.empty:
        if not expand and not as_dataframe:
            datasets = []
        elif not as_dataframe:
            datasets = {}
        return datasets

    if filters is not None:
        for k, v in filters.items():
            if k not in datasets.keys():
                util.logger.warning('filter field {} not found, continuing'.format(k))
                continue

            datasets = datasets.loc[datasets[k] == v]

    if queries is not None:
        for query in queries:
            datasets = datasets.query(query)

    if not expand and not as_dataframe:
        datasets = datasets['name'].tolist()
    elif not as_dataframe:
        datasets = datasets.to_dict(orient='index')

    return datasets


@add_async
def new_dataset(catalog_entry, collection, source=None, display_name=None,
                description=None, file_path=None, metadata=None, name=None):
    """Create a new dataset in a collection.

    Args:
        catalog_entry (string, Required):
            catalog_entry uri
        collection (string, Required):
            name of collection to create dataset in
        source (string, Optional, Default=None):
            type of the dataset such as timeseries or raster
        display_name (string, Optional, Default=None):
            display name for dataset
        description (string, Optional, Default=None):
            description of dataset
        file_path (string, Optional, Default=None):
            path location to save new dataset's data
        metadata (dict, Optional, Default=None):
            user defined metadata
        name (dict, Optional, Default=None):
            optionally pass in a UUID starting with d as name, otherwise it will be generated

    Returns:
        uri (string):
            uid of dataset
    """

    if collection not in get_collections():
        raise ValueError("Collection {} does not exist".format(collection))

    if not isinstance(catalog_entry, pd.DataFrame):
        catalog_entry = get_metadata(catalog_entry, as_dataframe=True)
    try:
        catalog_entry = catalog_entry['name'][0]
    except IndexError:
        raise ValueError('Entry {} dose not exist'.format(catalog_entry))

    name = name or util.uuid('dataset')
    assert name.startswith('d') and util.is_uuid(name)

    if source is None:
        source = static.DatasetSource.USER

    if display_name is None:
        display_name = name

    if metadata is None:
        metadata = {}

    quest_metadata = {
        'name': name,
        'collection': collection,
        'catalog_entry': catalog_entry,
        'source': source,
        'display_name': display_name,
        'description': description,
        'file_path': file_path,
        'metadata': metadata,
    }
    if source == static.DatasetSource.WEB_SERVICE:
        quest_metadata.update({'status': static.DatasetStatus.NOT_STAGED})

    db = get_db()
    with db_session:
        db.Dataset(**quest_metadata)

    return name


def stage_for_download(uris, options=None):
    """Apply download options before downloading
    Args:
        uris (string or list, Required):
            uris of datasets to stage for download

        options (dict or list of dicts, Optional, Default=None):
            options to be passed to quest.api.download function specified for each dataset

            If options is a dict, then apply same options to all datasets,
            else each dict in list is used for each respective dataset

    Returns:
        uris (list):
            staged dataset uids
    """
    uris = util.listify(uris)
    display_name = None
    datasets = []

    # TODO classify uris and ensure only datasets

    if not isinstance(options, list):
        options = [options] * len(uris)

    db = get_db()

    for dataset_uri, kwargs in zip(uris, options):
        if isinstance(kwargs, param.Parameterized):
            kwargs = dict(kwargs.get_param_values())

        dataset_metadata = get_metadata(dataset_uri)[dataset_uri]

        parameter = kwargs.get('parameter') if kwargs else None
        parameter_name = parameter or 'no_parameter'

        if dataset_metadata['display_name'] == dataset_uri:
            catalog_entry = dataset_metadata['catalog_entry']
            provider, service, _ = util.parse_service_uri(catalog_entry)
            display_name = '{0}-{1}-{2}'.format(provider, parameter_name, dataset_uri[:7])

        quest_metadata = {
            'display_name': display_name or dataset_metadata['display_name'],
            'options': kwargs,
            'status': static.DatasetStatus.STAGED,
            'parameter': parameter
        }

        with db_session:
            dataset = db.Dataset[dataset_uri]
            dataset.set(**quest_metadata)

        datasets.append(dataset_uri)

    return datasets


def describe_dataset():
    """Show metadata associated with downloaded dataset.

    This metadata includes as well as the quest function and kwargs used to
    generate the dataset.

    NOTIMPLEMENTED

    """
    pass


def open_dataset(dataset, fmt=None, **kwargs):
    """Open the dataset and return in format specified by fmt

    Args:
        dataset (string, Required):
            uid of dataset to be opened
        fmt (string, Optional, Default=None)
             format in which dataset should be returned
             will raise NotImplementedError if format requested is not possible

    Returns:
        data (pandas dataframe, json, or dict, Default=dataframe):
            contents of dataset

    """
    m = get_metadata(dataset).get(dataset)
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
        raise ValueError('No dataset file found')

    if file_format not in list_plugins(static.PluginType.IO):
        raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins(static.PluginType.IO, file_format)[file_format]
    return io.open(path, fmt=fmt, **kwargs)


@add_async
def visualize_dataset(dataset, update_cache=False, **kwargs):
    """Visualize the dataset as a matplotlib/bokeh plot.

    Check for existence of dataset on disk and call appropriate file format
    driver.

    Args:
        dataset (string, Required):
            uri of dataset to be visualized
        update_cache (bool, Optional, Default=False):
            currently unused
        kwargs:
            optional download kwargs

    Returns:
        path (string):
            path to the  newly visualized dataset

    """
    m = get_metadata(dataset).get(dataset)
    visualization_path = m.get('visualization_path')

    # TODO if vizualize_dataset is called with different options for a given
    # dataset the update cache.
    # if update_cache or visualization_path is None:
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
            raise ValueError('No dataset file found')

    if file_format not in list_plugins(static.PluginType.IO):
            raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins(static.PluginType.IO, file_format)[file_format]

    title = m.get('display_name')
    if title is None:
        title = dataset

    if 'timeseries' in file_format:
        visualization_path = io.visualize(path, title=title, **kwargs)
    else:
        visualization_path = io.visualize(path, **kwargs)
    quest_metadata = {'visualization_path': visualization_path}
    update_metadata(dataset, quest_metadata=quest_metadata)

    return visualization_path


def get_visualization_options(dataset, fmt='json'):
    """Return visualization available options for dataset.

    Args:
        dataset (string, Required):
            uid of dataset
        fmt (string, Required, Default='json'):
            format in which to return options

    Returns:
        get_visualization_options  (dict):
            options that can be specified when calling
            quest.api.visualize_dataset
    """
    m = get_metadata(dataset).get(dataset)
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
        raise ValueError('No dataset file found')

    if file_format not in list_plugins(static.PluginType.IO):
        raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins(static.PluginType.IO, file_format)[file_format]

    return io.visualize_options(path, fmt)
