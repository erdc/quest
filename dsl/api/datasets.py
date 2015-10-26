from .. import util


def download_dataset(source_uri, target_uri=None, **kwargs):
    """
    source_uri: must contain feature, if no parameter the download all parameters

    if source_uri is a collection then generate path from collection. 

    target_uri must either point to a collection or path

    If source uri is not a collection then target_uri must be specified
    """
    source_uri = util.parse_uri(source_uri)
    provider = source_uri['uid']
    service = source_uri['service']
    feature = source_uri['feature']
    parameter = source_uri['parameter']

    if target_uri is None:
        raise NotImplementedError

    if target_uri.lower().startswith('file://'):
        path = target_uri.split('file://')[-1]

    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset(path, service, feature, parameter, **kwargs)


def download_dataset_options(source_uri):
    source_uri = util.parse_uri(source_uri)
    provider = source_uri['name']
    service = source_uri['service']
    feature = source_uri['feature']
    parameter = source_uri['parameter']
    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset_options(service)


def update_dataset():
    pass


def describe_dataset():
    pass


def open_dataset():
    pass


def view_dataset():
    pass