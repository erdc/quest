import pytest
from types import ModuleType

from pandas import DataFrame

from data import DOWNLOAD_OPTIONS_FROM_ALL_SERVICES, SERVICE, CATALOG_ENTRY, DATASET, DATASET_METADATA

from quest.static import DatasetStatus

ACTIVE_PROJECT = 'test_data'

pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


def test_download_datasets():
    pass
    # TODO


@pytest.mark.parametrize('service, options', [(k, v) for k, v in DOWNLOAD_OPTIONS_FROM_ALL_SERVICES.items()])
def test_download_options_for_services(api, service, options):
    actual = api.get_download_options(service)[service]
    expected = options
    assert actual == expected


def test_download_options(api, reset_settings):
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
    new_dataset = api.new_dataset(CATALOG_ENTRY, 'col1')
    datasets = api.get_datasets()
    try:
        actual = len(datasets)
        expected = 2
        assert actual == expected

        assert new_dataset in datasets
    finally:
        api.delete(new_dataset)


def test_stage_for_download(api):
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
    pass


def test_open_dataset(api):
    pass


def test_visualize_dataset(api):
    pass


def test_visualize_dataset_options(api, dataset_save_path):
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
