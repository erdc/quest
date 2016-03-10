"""Datasets API functions."""
from jsonrpc import dispatcher

from .. import util
from . import db
from .projects import active_db


def download(feature, parameter=None, save_path=None, async=False, **kwargs):
    """Download dataset and save it locally.

    Parameters
    ----------
        feature: str
            uri of feature within service or collection.
            Ii=f no parameter is specified then all parameters are downloaded
            included. If feature is not part of a collection then save_path must
            be specified. save_path is ignored if feature is in collection.
        save_path: ``None`` or str
            filepath to save data
        async: bool (default False)
            If true download in background

    Return
    ------
        uri: string
            uri or handle of downloaded dataset

    Examples:
        TODO add examples

    """
    if source_uri.startswith('collection'):
        source = get_features(feature)['_service_uri_']
    else:
        source = source_uri

    source_uri = util.parse_uri(source)

    provider, service = source_uri['name'].split()
    feature = source_uri['feature']

    if target_uri is None:
        raise NotImplementedError

    if target_uri.lower().startswith('file://'):
        path = target_uri.split('file://')[-1]

    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset(path, service, feature, parameter, **kwargs)


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
    uri = util.parse_uri(feature)
    provider, service = uri['name'].split(':')
    # feature = uri['feature']
    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset_options(service)


@dispatcher.add_method
def new_dataset(feature, display_name=None, save_path=None, metadata=None):
    """Create a new dataset at a feature.

    Args:
        feature (string): uri of feature in collection

    Returns:
        uid of dataset
    """
    uri = util.parse_uri(feature)
    if uri['resource']!='collection':
        raise ValueError('Please add feature to a collection first')

    name = util.uuid()

    if dsl_metadata is None:
        dsl_metadata = {}

    dsl_metadata.update({'type': 'dataset'})
    db.upsert(active_db, 'datasets', name, dsl_metadata, metadata)

    return uid



def stage_for_download(datasets, download_options=None):
    """
    """
    datasets = util.listify(datasets)

    for datasets in datasets:
        dsl_metadata = {
            'download_options': download_options,
            'status': 'ready to download',
        }
        db.upsert(dbpath, 'datasets', dataset, dsl_metadata=None, metadata=None)

    return


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
