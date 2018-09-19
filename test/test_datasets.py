import pytest
from types import ModuleType

from pandas import DataFrame

from data import DOWNLOAD_OPTIONS_FROM_ALL_SERVICES, SERVICE, CATALOG_ENTRY, DATASET, DATASET_METADATA

from quest.static import DatasetStatus

ACTIVE_PROJECT = 'test_data'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


def test_download_datasets():
    """download staged datasets.

    TODO: ASYNC NOT IMPLEMENTED

    Download datasets that have been staged with stage_for_download
    args:
        datasets (string, list): list of datasets to download

    return:
        status (dict): download status of datasets
    """
    pass
    # TODO


@pytest.mark.parametrize('service, options', [(k, v) for k, v in DOWNLOAD_OPTIONS_FROM_ALL_SERVICES.items()])
def test_download_options_for_services(api, service, options):
    actual = api.get_download_options(service)[service]
    expected = options
    assert actual == expected


def test_download_options(api, reset_settings):
    """List optional kwargs that can be specified when downloading a dataset

    Parameters
    ----------
        uris (string or list):
            uris of features or datasets

    Return
    ------
        download_options: dict
            download options that can be specified when calling
            api.stage_for_download or api.download

    Examples:
        TODO add examples
    """
    # test get download options from list of service uris
    services = api.get_services()
    result = api.get_download_options(services)
    actual = result
    expected = DOWNLOAD_OPTIONS_FROM_ALL_SERVICES
    assert actual == expected

    # test get download options from single service as string
    actual = api.get_download_options(SERVICE)
    expected = {SERVICE: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected

    # test get download options from dataset
    actual = api.get_download_options(DATASET)
    expected = {DATASET: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected


def test_get_datasets(api, dataset_save_path):
    """
    metadata=None, filters=None, as_dataframe=None
    """
    # test generic get datasets

    actual = api.get_datasets()
    expected = [DATASET]
    assert actual == expected

    actual = api.get_datasets(expand=True)
    expected = {DATASET: DATASET_METADATA}
    expected[DATASET].update({'file_path': dataset_save_path})
    assert expected[DATASET]['catalog_entry'] == actual[DATASET]['catalog_entry']
    assert expected[DATASET]['name'] == actual[DATASET]['name']
    # assert actual == expected
    if isinstance(api, ModuleType):  # i.e. not using the RPC server
        actual = api.get_datasets(as_dataframe=True)
        assert isinstance(actual, DataFrame)

    actual = api.get_datasets(filters={'name': DATASET})
    expected = [DATASET]
    assert actual == expected

    actual = api.get_datasets(filters={'name': 'not_found'})
    assert actual == []


def test_get_datasets_with_query(api):
    datasets = api.get_datasets(
        queries=['status == "{}" or status == "{}"'.format(DatasetStatus.DOWNLOADED, DatasetStatus.DERIVED)]
    )
    expected = 1
    assert len(datasets) == expected


def test_new_dataset(api):
    """Create a new dataset at a feature.

    Args:
        feature (string): uid of feature

    Returns:
        uid of dataset
    """
    new_dataset = api.new_dataset(CATALOG_ENTRY, 'col1')
    datasets = api.get_datasets()
    try:
        # test number of datasets
        actual = len(datasets)
        expected = 2
        assert actual == expected

        assert new_dataset in datasets
    finally:
        api.delete(new_dataset)


def test_stage_for_download(api):
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

    # test stage new dataset
    new_dataset = api.new_dataset(CATALOG_ENTRY, 'col1')
    try:
        api.stage_for_download(new_dataset)
        metadata = api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['status'] == DatasetStatus.STAGED

        # test set download_options
        download_options = {'parameter': 'streamflow'}
        api.stage_for_download(new_dataset, options=download_options)
        metadata = api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['options'] == download_options
        assert metadata[new_dataset]['status'] == DatasetStatus.STAGED
    finally:
        api.delete(new_dataset)

    # test stage list of datasets
    download_options = {'parameter': 'streamflow'}
    new_dataset = api.new_dataset(CATALOG_ENTRY, 'col1')
    new_dataset2 = api.new_dataset(CATALOG_ENTRY, 'col1')
    new_datasets = api.stage_for_download([new_dataset, new_dataset2], options=download_options)
    try:
        metadata = api.get_metadata(uris=new_datasets)
        for dataset, metadata in metadata.items():
            assert metadata['options'] == download_options
            assert metadata['status'] == DatasetStatus.STAGED

        # test different download options
        download_options = [{'parameter': 'streamflow'}, {'parameter': 'water_temperature:daily:mean'}]
        api.stage_for_download(new_datasets, options=download_options)
        metadata = api.get_metadata(uris=new_datasets)
        for i, dataset in enumerate(new_datasets):
            assert metadata[dataset]['options'] == download_options[i]
            assert metadata[dataset]['status'] == DatasetStatus.STAGED
    finally:
        api.delete(new_datasets)


def test_describe_dataset(api):
    """Show metadata associated with downloaded dataset.

    This metadata includes as well as the quest function and kwargs used to
    generate the dataset.

    NOTIMPLEMENTED

    """
    pass


def test_open_dataset(api):
    """Open the dataset as a python/VTK object. Not sure this is needed.

    NOTIMPLEMENTED
    """
    pass


def test_visualize_dataset(api):
    """Visualize the dataset as a matplotlib/bokeh plot.

    Check for existence of dataset on disk and call appropriate file format
    driver.
    """
    pass


def test_visualize_dataset_options(api, dataset_save_path):
    """Return visualization available options for dataset."""
    expected = {'type': 'object',
                'properties': {'end': {'default': '2018-09-15 16:00:00',
                                       'type': 'string',
                                       'description': 'end date'
                                       },
                               'start': {'default': '2018-08-15 16:00:00',
                                         'type': 'string',
                                         'description': 'start date'
                                         }
                               },
                'title': 'Timeseries Vizualization Options'
                }
    actual = api.get_visualization_options(DATASET)
    assert actual == expected
