"""Datasets API functions."""
import json
from jsonrpc import dispatcher
import os

from .. import util
from . import db
from .projects import active_db
from .metadata import get_metadata


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
        df = df['_service'] + '/' + df['_service_id']
        service_uri = df.tolist()[0]

    if save_path is None:
        pass

    provider, service, feature = util.parse_service_uri(service_uri)
    driver = util.load_drivers('services', names=provider)[provider].driver
    data = driver.download(service=service, feature=feature,
                           save_path=save_path, dataset=dataset, **kwargs)
    return data


def download_datasets(datasets, async=False):
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
    datasets = datasets[datasets['_dataset_type'] == 'download']
    features = datasets['_feature'].tolist()
    features = get_metadata(features, as_dataframe=True)
    datasets = datasets.join(features[[
                                '_service',
                                '_service_id',
                                '_collection'
                             ]],
                             on='_feature')
    project_path = os.path.split(active_db())[0]
    status = {}
    for idx, dataset in datasets.iterrows():
        collection_path = os.path.join(project_path, dataset['_collection'])
        feature_uri = dataset['_service'] + '/' + dataset['_service_id']
        try:
            kwargs = json.loads(dataset['_download_options'])
            if kwargs is not None:
                metadata = download(feature_uri,
                                    save_path=collection_path,
                                    dataset=idx, **kwargs)
            else:
                metadata = download(feature_uri,
                                    save_path=collection_path,
                                    dataset=idx)

            dsl_metadata = {
                'save_path': metadata.pop('save_path'),
                'file_format': metadata.pop('file_format'),
                'parameter': metadata.pop('parameter'),
                'download_status': 'downloaded',
                'download_message': 'success',
                }
        except Exception as e:
            dsl_metadata = {
                'download_status': 'failed download',
                'download_message': e.message,
                }
            raise
            metadata = None

        status[idx] = dsl_metadata['download_status']
        db.upsert(active_db(), 'datasets', idx, dsl_metadata=dsl_metadata,
                  metadata=metadata)

    return status


def download_options(uris):
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
                feature = get_metadata(uri)[uri]['_feature']

            df = get_metadata(feature, as_dataframe=True)[0]
            df = df['_service'] + '/' + df['_service_id']
            service_uri = df.tolist()[0]

        provider, service, feature = util.parse_service_uri(service_uri)
        driver = util.load_drivers('services', names=provider)[provider].driver
        download_options[uri] = driver.download_options(service)

    return download_options


@dispatcher.add_method
def get_datasets(metadata=None, filters=None, as_dataframe=None):
    """
    """
    datasets = db.read_all(active_db(), 'datasets', as_dataframe=True)
    features = db.read_all(active_db(), 'features', as_dataframe=True)
    datasets = datasets.join(features['_collection'], on='_feature')

    if filters is not None:
        for k, v in filters.items():
            key = '_{}'.format(k)
            if key not in datasets.keys():
                print 'filter field {} not found, continuing'.format(k)
                continue

            datasets = datasets.ix[datasets[key] == v]

    if not metadata and not as_dataframe:
        datasets = datasets['_name'].tolist()
    elif not as_dataframe:
        # reformat metadata
        datasets = util.to_metadata(datasets)

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
    if db.read_data(active_db(), 'features', feature) is None:
        raise ValueError('feature {} does not exist'.format(feature))

    name = util.uuid('dataset')
    if dataset_type is None:
        dataset_type = 'user_created'

    if display_name is None:
        display_name = name

    dsl_metadata = {
        'feature': feature,
        'dataset_type': dataset_type,
        'display_name': display_name,
        'description': description,
    }
    if dataset_type == 'download':
        dsl_metadata.update({'download_status': 'not staged'})

    db.upsert(active_db(), 'datasets', name, dsl_metadata, metadata)

    return name


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

    for uri, kwargs in zip(uris, download_options):
        # if uid is a feature, create new dataset
        dataset_uri = uri
        if uri.startswith('f'):
            dataset_uri = new_dataset(uri, dataset_type='download')

        dsl_metadata = {
            'download_options': json.dumps(kwargs),
            'download_status': 'staged for download',
        }
        db.upsert(active_db(), 'datasets', dataset_uri,
                  dsl_metadata=dsl_metadata)
        datasets.append(dataset_uri)

    return datasets


def describe_dataset():
    """Show metadata associated with downloaded dataset.

    This metadata includes as well as the dsl function and kwargs used to
    generate the dataset.

    NOTIMPLEMENTED

    """
    pass


def open_dataset():
    """Open the dataset as a python/VTK object. Not sure this is needed.

    NOTIMPLEMENTED
    """
    pass


def vizualize_dataset():
    """Vizualize the dataset as a matplotlib/bokeh plot.

    NOTIMPLEMENTED
    """
    pass
