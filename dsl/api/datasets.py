"""Datasets API functions."""
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
        service_uri = get_metadata(feature, as_dataframe=True)
        service_uri = service_uri['_service_uri_'].tolist()[0]

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
    datasets = datasets[datasets['_dataset_type_'] == 'download']
    features = datasets['_feature_'].tolist()
    features = get_metadata(features, as_dataframe=True)
    datasets = datasets.join(features[['_service_uri_', '_collection_']],
                             on='_feature_')
    project_path = os.path.split(active_db())[0]
    status = {}
    for idx, dataset in datasets.iterrows():
        collection_path = os.path.join(project_path, dataset['_collection_'])
        try:
            metadata = download(dataset['_service_uri_'],
                                save_path=collection_path,
                                dataset=idx,
                                )

            dsl_metadata = {
                'save_path': metadata.pop('save_path'),
                'file_format': metadata.pop('file_format'),
                'download_status': 'downloaded',
                'download_message': 'success',
                }
        except Exception as e:
            dsl_metadata = {
                'download_status': 'failed download',
                'download_message': e.message,
                }
            metadata = None

        status[idx] = dsl_metadata['download_status']
        db.upsert(active_db(), 'datasets', idx, dsl_metadata=dsl_metadata,
                  metadata=metadata)

    return status

def download_options(feature):
    """List optional kwargs that can be specified when downloading a dataset

    Parameters
    ----------
        feature: str
            uri of feature in webservice or collection.

    Return
    ------
        kwargs: dict
            Optional kwargs that can be specified when calling
            dsl.api.download

    Examples:
        TODO add examples
    """
    service_uri = feature
    if not service_uri.startswith('svc://'):
        service_uri = get_metadata(feature, as_dataframe=True)
        service_uri = service_uri['_service_uri_'].tolist()[0]

    provider, service, feature = util.parse_service_uri(service_uri)
    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset_options(service)


@dispatcher.add_method
def get_datasets(filters=None):
    """
    """
    datasets = db.read_all(active_db(), 'datasets', as_dataframe=True)
    features = db.read_all(active_db(), 'features', as_dataframe=True)
    datasets = datasets.join(features['_collection_'], on='_feature_')

    if filters is None:
        return datasets['_name_'].tolist()

    for k, v in filters.items():
        key = '_{}_'.format(k)
        if key not in datasets.keys():
            print 'filter field {} not found, continuing'.format(k)
            continue

        datasets = datasets.ix[datasets[key] == v]

    return datasets['_name_'].tolist()


@dispatcher.add_method
def new_dataset(feature, dataset_type=None, display_name=None, save_path=None, metadata=None):
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

    dsl_metadata = {
        'feature': feature,
        'dataset_type': dataset_type,
    }
    if dataset_type == 'download':
        dsl_metadata.update({'download_status': 'not staged'})

    db.upsert(active_db(), 'datasets', name, dsl_metadata, metadata)

    return name


def stage_for_download(uids, download_kwargs=None):
    """
    args:
        uids (string or list): uids of features/datasets to stage for download,
            if uid is a feature a new dataset will be created.
        download_kwargs (dict or list of dicts): kwargs to be passed to the
            download function specified for each dataset. if dict then apply
            same kwargs to all datasets, else each dict in list is used for
            respective dataset

    return:
        uids (list): staged dataset uids
    """
    uids = util.listify(uids)
    datasets = []

    if not isinstance(download_kwargs, list):
        download_kwargs = [download_kwargs] * len(uids)

    for uid, kwargs in zip(uids, download_kwargs):
        # if uid is a feature, create new dataset
        dataset_uid = uid
        if uid.startswith('f'):
            dataset_uid = new_dataset(uid, dataset_type='download')

        dsl_metadata = {
            'download_kwargs': kwargs,
            'download_status': 'staged for download',
        }
        db.upsert(active_db(), 'datasets', dataset_uid,
                  dsl_metadata=dsl_metadata)
        datasets.append(dataset_uid)

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
