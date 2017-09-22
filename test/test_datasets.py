import os
import pytest
from types import ModuleType

from pandas import DataFrame


ACTIVE_PROJECT = 'test_data'
SERVICE = 'svc://usgs-nwis:iv'
FEATURE = 'f92ad0e35d04402ab1b1d4621b48a636'
DATASET = 'df5c3df3229441fa9c779443f03635e7'


pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


@pytest.fixture
def dataset_save_path(api, reset_projects_dir):
    save_path = os.path.join(reset_projects_dir['BASE_DIR'], 'projects/test_data/col1/usgs-nwis/iv/df5c3df3229441fa9c779443f03635e7.h5')
    api.update_metadata(uris=DATASET, quest_metadata={'file_path': save_path})

    return save_path


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


DOWNLOAD_OPTIONS_FROM_ALL_SERVICES = \
{'svc://nasa:srtm-3-arc-second': {},
 'svc://nasa:srtm-30-arc-second': {},
 'svc://ncdc:ghcn-daily': {'properties': [{'bounds': None,
    'default': 'null',
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': 'null',
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('air_temperature:daily:mean', 'air_temperature:daily:mean'),
     ('air_temperature:daily:minimum', 'air_temperature:daily:minimum'),
     ('air_temperature:daily:total', 'air_temperature:daily:total'),
     ('rainfall:daily:total', 'rainfall:daily:total'),
     ('snow_depth:daily:total', 'snow_depth:daily:total'),
     ('snowfall:daily:total', 'snowfall:daily:total')],
    'type': 'ObjectSelector'}],
  'title': 'NCDC GHCN Daily Download Options'},
 'svc://ncdc:gsod': {'properties': [{'bounds': None,
    'default': 'null',
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': 'null',
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('air_temperature:daily:max', 'air_temperature:daily:max'),
     ('air_temperature:daily:min', 'air_temperature:daily:min'),
     ('rainfall:daily:total', 'rainfall:daily:total'),
     ('snow_depth:daily:total', 'snow_depth:daily:total')],
    'type': 'ObjectSelector'}],
  'title': 'NCDC GSOD Download Options'},
 'svc://noaa:coops-meteorological': {'properties': [{'bounds': None,
    'default': 'null',
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': 'null',
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('air_temperature', 'air_temperature'),
     ('barometric_pressure', 'barometric_pressure'),
     ('collective_rainfall', 'collective_rainfall'),
     ('direction_of_sea_water_velocity', 'direction_of_sea_water_velocity'),
     ('relative_humidity', 'relative_humidity'),
     ('sea_water_electric_conductivity', 'sea_water_electric_conductivity'),
     ('sea_water_speed', 'sea_water_speed'),
     ('sea_water_temperature', 'sea_water_temperature'),
     ('visibility_in_air', 'visibility_in_air'),
     ('wind_from_direction', 'wind_from_direction'),
     ('wind_speed', 'wind_speed'),
     ('wind_speed_from_gust', 'wind_speed_from_gust')],
    'type': 'ObjectSelector'}],
  'title': 'NOAA COOPS Download Options'},
 'svc://noaa:coops-water': {'properties': [{'bounds': None,
    'default': 'null',
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': 'null',
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('predicted_waterLevel', 'predicted_waterLevel'),
     ('sea_surface_height_amplitude', 'sea_surface_height_amplitude')],
    'type': 'ObjectSelector'},
   {'default': '"6"',
    'description': 'time interval',
    'name': 'interval',
    'range': [('6', '6'), ('60', '60')],
    'type': 'ObjectSelector'},
   {'default': '"Mean Lower_Low Water"',
    'description': 'datum',
    'name': 'datum',
    'range': [('Great Diurnal Range', 'Great Diurnal Range'),
     ('Greenwich High Water Interval( in Hours)',
      'Greenwich High Water Interval( in Hours)'),
     ('Greenwich Low Water Interval( in Hours)',
      'Greenwich Low Water Interval( in Hours)'),
     ('Mean Diurnal High Water Inequality',
      'Mean Diurnal High Water Inequality'),
     ('Mean Diurnal Low Water Inequality',
      'Mean Diurnal Low Water Inequality'),
     ('Mean Diurnal Tide L0evel', 'Mean Diurnal Tide L0evel'),
     ('Mean High Water', 'Mean High Water'),
     ('Mean Higher - High Water', 'Mean Higher - High Water'),
     ('Mean Low Water', 'Mean Low Water'),
     ('Mean Lower_Low Water', 'Mean Lower_Low Water'),
     ('Mean Range of Tide', 'Mean Range of Tide'),
     ('Mean Sea Level', 'Mean Sea Level'),
     ('Mean Tide Level', 'Mean Tide Level'),
     ('North American Vertical Datum', 'North American Vertical Datum'),
     ('Station Datum', 'Station Datum')],
    'type': 'ObjectSelector'},
   {'default': '"R"',
    'description': 'quality',
    'name': 'quality',
    'range': [('Preliminary', 'Preliminary'),
     ('Verified', 'Verified'),
     ('R', 'R')],
    'type': 'ObjectSelector'}],
  'title': 'NOAA COOPS Download Options'},
 'svc://noaa:ndbc': {'properties': [{'bounds': None,
    'default': 'null',
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': 'null',
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('air_pressure', 'air_pressure'),
     ('air_temperature', 'air_temperature'),
     ('eastward_wind', 'eastward_wind'),
     ('northward_wind', 'northward_wind'),
     ('sea_surface_temperature', 'sea_surface_temperature'),
     ('water_level', 'water_level'),
     ('wave_height', 'wave_height'),
     ('wind_direction', 'wind_direction'),
     ('wind_from_direction', 'wind_from_direction'),
     ('wind_speed_of_gust', 'wind_speed_of_gust')],
    'type': 'ObjectSelector'}],
  'title': 'NOAA National Data Buoy Center Download Options'},
 'svc://usgs-ned:1-arc-second': {},
 'svc://usgs-ned:13-arc-second': {},
 'svc://usgs-ned:19-arc-second': {},
 'svc://usgs-ned:alaska-2-arc-second': {},
 'svc://usgs-nlcd:2001': {},
 'svc://usgs-nlcd:2006': {},
 'svc://usgs-nlcd:2011': {},
 'svc://usgs-nwis:dv': {'properties': [{'bounds': None,
    'default': '30',
    'description': 'period date',
    'name': 'period',
    'type': 'Integer'},
   {'bounds': None,
    'default': None,
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': None,
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('streamflow:mean:daily', 'streamflow:mean:daily'),
     ('water_temperature:daily:max', 'water_temperature:daily:max'),
     ('water_temperature:daily:mean', 'water_temperature:daily:mean'),
     ('water_temperature:daily:min', 'water_temperature:daily:min')],
    'type': 'ObjectSelector'}],
  'title': 'NWIS Daily Values Service Download Options'},
 'svc://usgs-nwis:iv': {'properties': [{'bounds': None,
    'default': '30',
    'description': 'period date',
    'name': 'period',
    'type': 'Integer'},
   {'bounds': None,
    'default': None,
    'description': 'end date',
    'name': 'end',
    'type': 'Date'},
   {'bounds': None,
    'default': None,
    'description': 'start date',
    'name': 'start',
    'type': 'Date'},
   {'default': None,
    'description': 'parameter',
    'name': 'parameter',
    'range': [('gage_height', 'gage_height'),
     ('streamflow', 'streamflow'),
     ('water_temperature', 'water_temperature')],
    'type': 'ObjectSelector'}],
  'title': 'NWIS Instantaneous Values Service Download Options'}}


def test_download_options(api):
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
    result = api.download_options(services)
    for service in services:
        actual = result[service]
        expected = DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[service]
        print(service)
        assert actual == expected

    # test get download options from single service as string
    actual = api.download_options(SERVICE)
    expected = {SERVICE: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected

    # test get download options from feature
    actual = api.download_options(FEATURE)
    expected = {FEATURE: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected

    # test get download options from dataset
    actual = api.download_options(DATASET)
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
    expected = {DATASET: {'download_status': 'downloaded',
                                             'download_message': 'success',
                                             'name': 'df5c3df3229441fa9c779443f03635e7',
                                             'file_format': 'timeseries-hdf5',
                                             'datatype': 'timeseries',
                                             'feature': 'f92ad0e35d04402ab1b1d4621b48a636',
                                             'collection': 'test_data',
                                             'download_options': '{"parameter": "streamflow"}',
                                             'dataset_type': 'download',
                                             'timezone': 'utc',
                                             'unit': 'ft3/s',
                                             'display_name': 'df5c3df3229441fa9c779443f03635e7',
                                             'parameter': 'streamflow',
                                             'metadata': {}
                          }
                }
    expected[DATASET].update({'file_path': dataset_save_path})
    assert expected[DATASET]['feature'] == actual[DATASET]['feature']
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


def test_new_dataset(api):
    """Create a new dataset at a feature.

    Args:
        feature (string): uid of feature

    Returns:
        uid of dataset
    """
    new_dataset = api.new_dataset(FEATURE)
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
    new_dataset = api.new_dataset(FEATURE)
    try:
        api.stage_for_download(new_dataset)
        metadata = api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['status'] == 'staged for download'

        # test set download_options
        download_options = {'parameter': 'streamflow'}
        api.stage_for_download(new_dataset, options=download_options)
        metadata = api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['options'] == download_options
        assert metadata[new_dataset]['status'] == 'staged for download'
    finally:
        api.delete(new_dataset)

    # test stage new dataset from feature
    new_dataset = api.stage_for_download(FEATURE)[0]
    try:
        metadata = api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['status'] == 'staged for download'
    finally:
        api.delete(new_dataset)

    # test stage list of datasets/features
    download_options = {'parameter': 'streamflow'}
    new_dataset = api.new_dataset(FEATURE)
    new_datasets = api.stage_for_download([FEATURE, new_dataset], options=download_options)
    try:
        metadata = api.get_metadata(uris=new_datasets)
        for dataset, metadata in metadata.items():
            assert metadata['options'] == download_options
            assert metadata['status'] == 'staged for download'

        # test different download options
        download_options = [{'parameter': 'streamflow'}, {'parameter': 'water_temperature:daily:mean'}]
        api.stage_for_download(new_datasets, options=download_options)
        metadata = api.get_metadata(uris=new_datasets)
        for i, dataset in enumerate(new_datasets):
            assert metadata[dataset]['options'] == download_options[i]
            assert metadata[dataset]['status'] == 'staged for download'
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
                'properties': {'end': {'default': '2017-01-02 05:00:00',
                                       'type': 'string',
                                       'description': 'end date'
                                       },
                               'start': {'default': '2017-01-01 05:00:00',
                                         'type': 'string',
                                         'description': 'start date'
                                         }
                               },
                'title': 'Timeseries Vizualization Options'
                }
    actual = api.visualize_dataset_options(DATASET)
    assert actual == expected
