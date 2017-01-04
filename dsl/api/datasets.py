"""Datasets API functions."""
import json
from jsonrpc import dispatcher
import os

from .. import util
from .database import get_db, db_session
import pandas as pd
from .metadata import get_metadata, update_metadata
from .projects import _get_project_dir


@dispatcher.add_method
def download(feature, save_path, dataset=None, async=False, **kwargs):
    """Download dataset and save it locally.

    Parameters
    ----------
        feature (string):
            uri of feature within service or collection.
        save_path: ``None`` or str
            filepath to save data
        dataset (string, optional):
        async: bool (default False)
            If true download in background

        kwargs:
            optional download kwargs

    Return
    ------
        data (dict):
            details of downloaded data

    Examples:
        TODO add examples

    """
    service_uri = feature
    if not service_uri.startswith('svc://'):
        df = get_metadata(feature, as_dataframe=True)[0]
        df = df['service'] + '/' + df['service_id']
        service_uri = df.tolist()[0]

    if save_path is None:
        pass

    provider, service, feature = util.parse_service_uri(service_uri)
    driver = util.load_services()[provider]
    data = driver.download(service=service, feature=feature,
                           save_path=save_path, dataset=dataset, **kwargs)
    return data


@dispatcher.add_method
def download_datasets(datasets, async=False, raise_on_error=False):
    """download staged datasets.

    TODO: ASYNC NOT IMPLEMENTED

    Download datasets that have been staged with stage_for_download
    args:
        datasets (string, list): list of datasets to download

    return:
        status (dict): download status of datasets
    """
    datasets = get_metadata(datasets, as_dataframe=True)

    # filter out non download datasets
    datasets = datasets[datasets['datatype'] == 'download']
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
            kwargs = json.loads(dataset['options'])
            if kwargs is not None:
                all_metadata = download(feature_uri,
                                    save_path=collection_path,
                                    dataset=idx, **kwargs)
            else:
                all_metadata = download(feature_uri,
                                    save_path=collection_path,
                                    dataset=idx)

            metadata = all_metadata.pop('metadata', None)
            dsl_metadata = all_metadata
            dsl_metadata.update({
                'status': 'downloaded',
                'message': 'success',
                })
        except Exception as e:
            if raise_on_error:
                raise

            dsl_metadata = {
                'status': 'failed download',
                'message': str(e),
                }

            metadata = None

        status[idx] = dsl_metadata['status']

        dsl_metadata.update({'metadata': metadata})

        with db_session:
            dataset = db.Dataset[idx]
            dataset.set(**dsl_metadata)

    return status


@dispatcher.add_method
def download_options(uris, fmt='json-schema'):
    """List optional kwargs that can be specified when downloading a dataset

    Parameters
    ----------
        uris (string or list):
            uris of features or datasets

    Return
    ------
        download_options: dict
            download options that can be specified when calling
            dsl.api.stage_for_download or dsl.api.download

    Examples:
        TODO add examples
    """
    uris = util.listify(uris)
    download_options = {}
    for uri in uris:
        service_uri = uri
        if not service_uri.startswith('svc://'):
            feature = uri
            if feature.startswith('d'):
                feature = get_metadata(uri)[uri]['feature']

            df = get_metadata(feature, as_dataframe=True).ix[0]
            df = df['service'] + '/' + df['service_id']
            service_uri = df

        provider, service, feature = util.parse_service_uri(service_uri)
        driver = util.load_services()[provider]
        download_options[uri] = driver.download_options(service, fmt)

    return download_options


@dispatcher.add_method
def get_datasets(expand=None, filters=None, as_dataframe=None):
    """
    """
    db = get_db()
    with db_session:
        datasets = [dict(d.to_dict(), **{'collection': d.feature.collection.name}) for d in db.Dataset.select()]
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
                print('filter field {} not found, continuing'.format(k))
                continue

            datasets = datasets.ix[datasets[k] == v]

    if not expand and not as_dataframe:
        datasets = datasets['name'].tolist()
    elif not as_dataframe:
        datasets = datasets.to_dict(orient='index')

    return datasets


@dispatcher.add_method
def new_dataset(feature, dataset_type=None, display_name=None,
                description=None, save_path=None, metadata=None):
    """Create a new dataset at a feature.

    Args:
        feature (string): uid of feature

    Returns:
        uid of dataset
    """
    # check if feature exists
    db = get_db()
    with db_session:
        f = db.Feature[feature]
        if f is None:
            raise ValueError('feature {} does not exist'.format(feature))

    name = util.uuid('dataset')
    if dataset_type is None:
        dataset_type = 'user_created'

    if display_name is None:
        display_name = name

    if metadata is None:
        metadata = {}

    dsl_metadata = {
        'name': name,
        'feature': feature,
        'datatype': dataset_type,
        'display_name': display_name,
        'description': description,
        'file_path': save_path,
        'metadata': metadata,
    }
    if dataset_type == 'download':
        dsl_metadata.update({'status': 'not staged'})

    with db_session:
        db.Dataset(**dsl_metadata)

    return name


@dispatcher.add_method
def stage_for_download(uris, download_options=None):
    """
    args:
        uris (string or list): uris of features/datasets to stage for download,
            if uri is a feature a new dataset will be created.
        download_kwargs (dict or list of dicts): kwargs to be passed to the
            download function specified for each dataset. if dict then apply
            same kwargs to all datasets, else each dict in list is used for
            respective dataset

    return:
        uris (list): staged dataset uids
    """
    uris = util.listify(uris)
    datasets = []

    if not isinstance(download_options, list):
        download_options = [download_options] * len(uris)

    db = get_db()

    for uri, kwargs in zip(uris, download_options):
        # if uid is a feature, create new dataset
        dataset_uri = uri
        if uri.startswith('f'):
            dataset_uri = new_dataset(uri, dataset_type='download')

        dsl_metadata = {
            'options': json.dumps(kwargs),
            'status': 'staged for download',
        }

        with db_session:
            dataset = db.Dataset[dataset_uri]
            dataset.set(**dsl_metadata)

        datasets.append(dataset_uri)

    return datasets


@dispatcher.add_method
def describe_dataset():
    """Show metadata associated with downloaded dataset.

    This metadata includes as well as the dsl function and kwargs used to
    generate the dataset.

    NOTIMPLEMENTED

    """
    pass


@dispatcher.add_method
def open_dataset(dataset, fmt=None):
    """Open the dataset and return in format specified by fmt

    will raise NotImplementedError if format requested is not possible
    """
    m = get_metadata(dataset).get(dataset)
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
        raise ValueError('No dataset file found')

    if file_format not in util.list_drivers('io'):
        raise ValueError('No reader available for: %s' % file_format)

    io = util.load_drivers('io', file_format)
    io = io[file_format].driver
    return io.open(path, fmt=fmt)


@dispatcher.add_method
def visualize_dataset(dataset, update_cache=False, **kwargs):
    """Visualize the dataset as a matplotlib/bokeh plot.

    Check for existence of dataset on disk and call appropriate file format
    driver.
    """
    m = get_metadata(dataset).get(dataset)
    visualization_path = m.get('visualization_path')

    # TODO if vizualize_dataset is called with different options for a given
    # dataset the update cache.
    #if update_cache or visualization_path is None:
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
            raise ValueError('No dataset file found')

    if file_format not in util.list_drivers('io'):
            raise ValueError('No reader available for: %s' % file_format)

    io = util.load_drivers('io', file_format)
    io = io[file_format].driver

    title = m.get('display_name')
    if title is None:
        title = dataset

    visualization_path = io.visualize(path, title=title, **kwargs)
    dsl_metadata = {'visualization_path': visualization_path}
    update_metadata(dataset, dsl_metadata=dsl_metadata)

    return visualization_path


@dispatcher.add_method
def visualize_dataset_options(dataset, fmt='json-schema'):
    """Return visualization available options for dataset."""
    m = get_metadata(dataset).get(dataset)
    file_format = m.get('file_format')
    path = m.get('file_path')

    if path is None:
        raise ValueError('No dataset file found')

    if file_format not in util.list_drivers('io'):
        raise ValueError('No reader available for: %s' % file_format)

    io = util.load_drivers('io', file_format)
    io = io[file_format].driver

    return io.visualize_options(path, fmt)
