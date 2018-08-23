"""Datasets API functions."""

from quest.database.database import get_db, db_session, select_datasets
from ..plugins import load_providers, load_plugins, list_plugins
from ..util import logger, parse_service_uri, listify, uuid
from .metadata import get_metadata, update_metadata
from .projects import _get_project_dir
from quest.static import DatasetStatus
from .tasks import add_async
import pandas as pd
import os


@add_async
def download(feature, file_path, dataset=None, **kwargs):
    """Download dataset and save it locally.

    Args:
        feature (string, Required):
            uri of feature within a service or collection
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
    service_uri = feature
    if not service_uri.startswith('svc://'):
        df = get_metadata(feature, as_dataframe=True)[0]
        df = df['service'] + '/' + df['service_id']
        service_uri = df.tolist()[0]

    if file_path is None:
        pass

    provider, service, feature = parse_service_uri(service_uri)
    provider_plugin = load_providers()[provider]
    data = provider_plugin.download(service=service, feature=feature,
                                    file_path=file_path, dataset=dataset, **kwargs)
    return data


@add_async
def publish(publisher_uri, **kwargs):
    provider, publisher, feature = parse_service_uri(publisher_uri)
    provider_plugin = load_providers()[provider]
    data = provider_plugin.publish(publisher=publisher, **kwargs)
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

    # filter out non download datasets
    datasets = datasets[datasets['source'] == 'download']
    features = datasets['feature'].tolist()
    features = get_metadata(features, as_dataframe=True)
    datasets = datasets.join(features[[
                                'service',
                                'service_id',
                             ]],
                             on='feature')

    db = get_db()
    project_path = _get_project_dir()
    status = {}
    for idx, dataset in datasets.iterrows():
        collection_path = os.path.join(project_path, dataset['collection'])
        feature_uri = dataset['service'] + '/' + dataset['service_id']
        try:
            update_metadata(idx, quest_metadata={'status': DatasetStatus.PENDING})
            kwargs = dataset['options'] or dict()
            all_metadata = download(feature_uri,
                                    file_path=collection_path,
                                    dataset=idx, **kwargs)

            metadata = all_metadata.pop('metadata', None)
            quest_metadata = all_metadata
            quest_metadata.update({
                'status': DatasetStatus.DOWNLOADED,
                'message': 'success',
                })
        except Exception as e:
            if raise_on_error:
                raise

            quest_metadata = {
                'status': DatasetStatus.FAILED_DOWNLOAD,
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
            uris of features or datasets
        fmt (string, Required, Default='json'):
            format in which to return download_options. One of ['json', 'param']


    Returns:
        download_options (dict):
            download options that can be specified when calling
            quest.api.stage_for_download or quest.api.download
    """
    uris = listify(uris)
    options = {}
    for uri in uris:
        service_uri = uri
        if not service_uri.startswith('svc://'):
            feature = uri
            if feature.startswith('d'):
                feature = get_metadata(uri)[uri]['feature']

            df = get_metadata(feature, as_dataframe=True).iloc[0]
            df = df['service'] + '/' + df['service_id']
            service_uri = df

        provider, service, feature = parse_service_uri(service_uri)
        provider_plugin = load_providers()[provider]
        options[uri] = provider_plugin.get_download_options(service, fmt)

    return options


def get_publish_options(publish_uri, fmt='json'):
    uris = listify(publish_uri)
    options = {}
    for uri in uris:
        publish_uri = uri
        provider, publisher, feature = parse_service_uri(publish_uri)
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
                logger.warning('filter field {} not found, continuing'.format(k))
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
def new_dataset(feature, source=None, display_name=None,
                description=None, file_path=None, metadata=None):
    """Create a new dataset at a feature.

    Args:
        feature (string, Required):
            uid of a feature
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

    Returns:
        uri (string):
            uid of dataset
    """
    # check if feature exists
    db = get_db()
    with db_session:
        f = db.Feature[feature]
        if f is None:
            raise ValueError('feature {} does not exist'.format(feature))

    name = uuid('dataset')
    if source is None:
        source = 'user_created'

    if display_name is None:
        display_name = name

    if metadata is None:
        metadata = {}

    quest_metadata = {
        'name': name,
        'feature': feature,
        'source': source,
        'display_name': display_name,
        'description': description,
        'file_path': file_path,
        'metadata': metadata,
    }
    if source == 'download':
        quest_metadata.update({'status': DatasetStatus.NOT_STAGED})

    with db_session:
        db.Dataset(**quest_metadata)

    return name


def stage_for_download(uris, options=None):
    """Apply download options before downloading
    Args:
        uris (string or list, Required):
            uris of features/datasets to stage for download

            If uri is a feature, a new dataset will be created

        options (dict or list of dicts, Optional, Default=None):
            options to be passed to quest.api.download function specified for each dataset

            If options is a dict, then apply same options to all datasets,
            else each dict in list is used for each respective dataset

    Returns:
        uris (list):
            staged dataset uids
    """
    uris = listify(uris)
    display_name = None
    datasets = []

    if not isinstance(options, list):
        options = [options] * len(uris)

    db = get_db()

    for uri, kwargs in zip(uris, options):
        # if uid is a feature, create new dataset
        dataset_uri = uri
        if uri.startswith('f'):
            dataset_uri = new_dataset(uri, source='download')

        dataset_metadata = get_metadata(dataset_uri)[dataset_uri]

        parameter = kwargs.get('parameter') if kwargs else None
        parameter_name = parameter or "no_parameter"

        if dataset_metadata['display_name'] == dataset_uri:
            dataset_feature = dataset_metadata['feature']
            feature_metadata = get_metadata(dataset_feature)[dataset_feature]
            service = feature_metadata['service']
            provider, service, _ = parse_service_uri(service)
            display_name = '{0}-{1}-{2}'.format(provider, parameter_name, dataset_uri[:7])

        quest_metadata = {
            'display_name': display_name or dataset_metadata['display_name'],
            'options': kwargs,
            'status': DatasetStatus.STAGED,
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


def open_dataset(dataset, fmt=None):
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

    if file_format not in list_plugins('io'):
        raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins('io', file_format)[file_format]
    return io.open(path, fmt=fmt)


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

    if file_format not in list_plugins('io'):
            raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins('io', file_format)[file_format]

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

    if file_format not in list_plugins('io'):
        raise ValueError('No reader available for: %s' % file_format)

    io = load_plugins('io', file_format)[file_format]

    return io.visualize_options(path, fmt)
