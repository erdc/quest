from .. import util


def download_dataset(source_uri, target_uri=None, **kwargs):
    """Download dataset and save it locally

    Parameters
    ----------
        source_uri: str
            uri of webservice or collection. must contain feature but need 
            not contain a parameter, if no parameter then all parameters are
            included. If source uri is not a collection then target_uri must 
            be specified
        target_uri: ``None`` or str
            uri of target. If source_uri is a collection then this parameter
            is ignores. If source_uri is a webservice then target_uri must be a 
            filepath (i.e. file:///path/to/folder). (target_uri can also be a 
            different collection *NOTIMPLEMENTED*)
    
    Return
    ------
        msg: str Not sure need to check

    Examples:
        TODO add examples

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
    """List optional kwargs that can be specified when downloading a dataset

    Parameters
    ----------
        source_uri: str
            uri of webservice or collection. must contain feature but need 
            not contain a parameter, if no parameter then all parameters are
            included.
    
    Return
    ------
        kwargs: dict
            Optional kwargs that can be specified when calling dsl.api.download_dataset

    Examples:
        TODO add examples
    """
    source_uri = util.parse_uri(source_uri)
    provider = source_uri['name']
    service = source_uri['service']
    feature = source_uri['feature']
    parameter = source_uri['parameter']
    driver = util.load_drivers('services', names=provider)[provider].driver
    return driver.download_dataset_options(service)


def update_dataset():
    """Update metatata related to a downloaded dataset.
    NOTIMPLEMENTED
    """
    pass


def describe_dataset():
    """Show metadata associated with downloaded dataset as well as the dsl function
    and kwargs used to generate the dataset
    NOTIMPLEMENTED
    """
    pass


def open_dataset():
    """Open the dataset as a python/VTK object. Not sure this is needed
    NOTIMPLEMENTED
    """
    pass


def vizualize_dataset():
    """Vizualize the dataset as a matplotlib/bokeh plot.
    NOTIMPLEMENTED
    """
    pass