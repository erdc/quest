import os
import json
import pytest

from pandas import DataFrame
import dsl


ACTIVE_PROJECT = 'test_data'
SERVICE = 'svc://usgs-nwis:iv'
FEATURE = 'f92ad0e35d04402ab1b1d4621b48a636'
DATASET = 'df5c3df3229441fa9c779443f03635e7'


pytestmark = pytest.mark.usefixtures('reset_projects_dir', 'set_active_project')


@pytest.fixture
def dataset_save_path(reset_projects_dir):
    save_path = os.path.join(reset_projects_dir['BASE_DIR'], 'projects/test_data/test_data/usgs-nwis/iv/df5c3df3229441fa9c779443f03635e7')
    dsl.api.update_metadata(uris=DATASET, dsl_metadata={'file_path': save_path})

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


DOWNLOAD_OPTIONS_FROM_ALL_SERVICES = {'svc://nasa:srtm-3-arc-second': {},
                                      'svc://nasa:srtm-30-arc-second': {},
                                      'svc://ncdc:ghcn-daily': {'properties': {'end': {'description': 'end date',
                                                                                       'type': 'string'
                                                                                       },
                                                                               'parameter': {'description': 'parameter',
                                                                                             'enum': ['air_temperature:daily:mean',
                                                                                                      'air_temperature:daily:minimum',
                                                                                                      'air_temperature:daily:total',
                                                                                                      'rainfall:daily:total',
                                                                                                      'snow_depth:daily:total',
                                                                                                      'snowfall:daily:total',
                                                                                                      ],
                                                                                             'type': 'string'
                                                                                             },
                                                                               'start': {'description': 'start date',
                                                                                         'type': 'string'
                                                                                         }
                                                                               },
                                                                'title': 'NCDC Download Options',
                                                                'type': 'object'
                                                                },
                                      'svc://ncdc:gsod': {'properties': {'end': {'description': 'end date',
                                                                                 'type': 'string'
                                                                                 },
                                                                         'parameter': {'description': 'parameter',
                                                                                       'enum': ['air_temperature:daily:max',
                                                                                                'air_temperature:daily:min',
                                                                                                'rainfall:daily:total',
                                                                                                'snow_depth:daily:total',
                                                                                                ],
                                                                                       'type': 'string'
                                                                                       },
                                                                         'start': {'description': 'start date',
                                                                                   'type': 'string'
                                                                                   }
                                                                         },
                                                          'title': 'NCDC Download Options',
                                                          'type': 'object'
                                                          },
                                      'svc://noaa:coops-water':  {

                                                                                    "title": "NOAA Download Options",
                                                                                    "type": "object",
                                                                                    "properties": {
                                                                                        "parameter": {
                                                                                            "type": "string",
                                                                                            "enum": [ 'predicted_waterLevel',
                                                                                                      'sea_surface_height_amplitude'],
                                                                                            "description": "parameter",
                                                                                        },
                                                                                        "start": {
                                                                                            "type": "string",
                                                                                            "description": "start date",
                                                                                        },
                                                                                        "end": {
                                                                                            "type": "string",
                                                                                            "description": "end date",
                                                                                        },
                                                                                        "quality": {
                                                                                            "type": "string",
                                                                                            "description": "quality",
                                                                                            "options": ['Preliminary','Verified'],
                                                                                        },
                                                                                        "interval": {
                                                                                            "type": "string",
                                                                                            "type": "string",
                                                                                            "description": "time interval",
                                                                                            "options": ['6', '60'],
                                                                                        },
                                                                                        "datum": { #temporary hard coding
                                                                                            "type": "string",
                                                                                            "description": "time interval",
                                                                                            "options": [
                                                                                                        {'DHQ':'Mean Diurnal High Water Inequality'},
                                                                                                        {'DLQ':'Mean Diurnal Low Water Inequality'},
                                                                                                        {'DTL':'Mean Diurnal Tide L0evel'},
                                                                                                        {'GT':'Great Diurnal Range'},
                                                                                                        {'HWI':'Greenwich High Water Interval( in Hours)'},
                                                                                                        {'LWI':'Greenwich Low Water Interval( in Hours)'},
                                                                                                        {'MHHW':'Mean Higher - High Water'},
                                                                                                        {'MHW':'Mean High Water'},
                                                                                                        {'MLLW':'Mean Lower_Low Water'},
                                                                                                        {'MLW':'Mean Low Water'},
                                                                                                        {'MN':'Mean Range of Tide'},
                                                                                                        {'MSL':'Mean Sea Level'},
                                                                                                        {'MTL':'Mean Tide Level'},
                                                                                                        {'NAVD''North American Vertical Datum'},
                                                                                                        {'STND':'Station Datum'},
                                                                                                        ]
                                                                                        },
                                                                                    },
                                                                                },

                                      'svc://noaa:coops-meteorological': {'properties': {'end': {'description': 'end date',
                                                                                 'type': 'string'
                                                                                 },
                                                                          'parameter': {'description': 'parameter',
                                                                                           'enum': ['air_temperature',
                                                                                                    'barometric_pressure',
                                                                                                    'collective_rainfall',
                                                                                                    'direction_of_sea_water_velocity',
                                                                                                    'relative_humidity',
                                                                                                    'sea_water_electric_conductivity',
                                                                                                    'sea_water_speed',
                                                                                                    'sea_water_temperature',
                                                                                                    'visibility_in_air',
                                                                                                    'wind_from_direction',
                                                                                                    'wind_speed',
                                                                                                    'wind_speed_from_gust'],

                                                                                           'type': 'string'
                                                                                       },
                                                                         'start': {'description': 'start date',
                                                                                   'type': 'string'
                                                                                   }
                                                                         },
                                                          'title': 'NOAA Download Options',
                                                          'type': 'object'
                                                          },

                                      'svc://noaa:ndbc': {'properties': {'end': {'description': 'end date',
                                                                                 'type': 'string'
                                                                                 },
                                                                         'parameter': {'description': 'parameter',
                                                                                       'enum': ['air_pressure',
                                                                                                'air_temperature',
                                                                                                'eastward_wind',
                                                                                                'northward_wind',
                                                                                                'sea_surface_temperature',
                                                                                                'water_level',
                                                                                                'wave_height',
                                                                                                'wind_direction',
                                                                                                'wind_from_direction',
                                                                                                'wind_speed_of_gust',
                                                                                                ],
                                                                                       'type': 'string'
                                                                                       },
                                                                         'start': {'description': 'start date',
                                                                                   'type': 'string'
                                                                                   }
                                                                         },
                                                          'title': 'NOAA Download Options',
                                                          'type': 'object'
                                                          },
                                      'svc://usgs-ned:1-arc-second': {},
                                      'svc://usgs-ned:13-arc-second': {},
                                      'svc://usgs-ned:19-arc-second': {},
                                      'svc://usgs-ned:alaska-2-arc-second': {},
                                      'svc://usgs-nlcd:2001': {},
                                      'svc://usgs-nlcd:2006': {},
                                      'svc://usgs-nlcd:2011': {},
                                      'svc://usgs-nwis:dv': {'properties': {'end': {'description': 'end date',
                                                                                    'type': 'string'
                                                                                    },
                                                                            'parameter': {'description': 'parameter',
                                                                                          'enum': ['streamflow:mean:daily',
                                                                                                   'water_temperature:daily:max',
                                                                                                   'water_temperature:daily:mean',
                                                                                                   'water_temperature:daily:min',
                                                                                                   ],
                                                                                          'type': 'string'
                                                                                          },
                                                                            'period': {'description': 'period date',
                                                                                       'type': 'string'
                                                                                       },
                                                                            'start': {'description': 'start date',
                                                                                      'type': 'string'
                                                                                      }
                                                                            },
                                                             'title': 'USGS NWIS Download Options',
                                                             'type': 'object'
                                                             },
                                      'svc://usgs-nwis:iv': {'properties': {'end': {'description': 'end date',
                                                                                    'type': 'string'
                                                                                    },
                                                                            'parameter': {'description': 'parameter',
                                                                                          'enum': ['gage_height',
                                                                                                   'streamflow',
                                                                                                   'water_temperature',
                                                                                                   ],
                                                                                          'type': 'string'
                                                                                          },
                                                                            'period': {'description': 'period date',
                                                                                       'type': 'string'
                                                                                       },
                                                                            'start': {'description': 'start date',
                                                                                      'type': 'string'
                                                                                      }
                                                                            },
                                                             'title': 'USGS NWIS Download Options',
                                                             'type': 'object'
                                                             }
                                      }


def test_download_options():
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
    # test get download options from list of service uris
    services = dsl.api.get_services()
    result = dsl.api.download_options(services)
    for service in services:
        actual = result[service]
        expected = DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[service]
        assert actual == expected

    # test get download options from single service as string
    actual = dsl.api.download_options(SERVICE)
    expected = {SERVICE: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected

    # test get download options from feature
    actual = dsl.api.download_options(FEATURE)
    expected = {FEATURE: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected

    # test get download options from dataset
    actual = dsl.api.download_options(DATASET)
    expected = {DATASET: DOWNLOAD_OPTIONS_FROM_ALL_SERVICES[SERVICE]}
    assert actual == expected


def test_get_datasets(dataset_save_path):
    """
    metadata=None, filters=None, as_dataframe=None
    """
    # test generic get datasets

    actual = dsl.api.get_datasets()
    expected = [DATASET]
    assert actual == expected

    actual = dsl.api.get_datasets(expand=True)
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
    actual = dsl.api.get_datasets(as_dataframe=True)
    assert isinstance(actual, DataFrame)

    actual = dsl.api.get_datasets(filters={'name': DATASET})
    expected = [DATASET]
    assert actual == expected

    actual = dsl.api.get_datasets(filters={'name': 'not_found'})
    assert actual == []


def test_new_dataset():
    """Create a new dataset at a feature.

    Args:
        feature (string): uid of feature

    Returns:
        uid of dataset
    """
    new_dataset = dsl.api.new_dataset(FEATURE)
    datasets = dsl.api.get_datasets()
    try:
        # test number of datasets
        actual = len(datasets)
        expected = 2
        assert actual == expected

        assert new_dataset in datasets
    finally:
        dsl.api.delete(new_dataset)


def test_stage_for_download():
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
    new_dataset = dsl.api.new_dataset(FEATURE)
    try:
        dsl.api.stage_for_download(new_dataset)
        metadata = dsl.api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['status'] == 'staged for download'

        # test set download_options
        download_options = {'parameter': 'streamflow'}
        dsl.api.stage_for_download(new_dataset, download_options=download_options)
        metadata = dsl.api.get_metadata(uris=new_dataset)
        assert json.loads(metadata[new_dataset]['options']) == download_options
        assert metadata[new_dataset]['status'] == 'staged for download'
    finally:
        dsl.api.delete(new_dataset)

    # test stage new dataset from feature
    new_dataset = dsl.api.stage_for_download(FEATURE)[0]
    try:
        metadata = dsl.api.get_metadata(uris=new_dataset)
        assert metadata[new_dataset]['status'] == 'staged for download'
    finally:
        dsl.api.delete(new_dataset)

    # test stage list of datasets/features
    download_options = {'parameter': 'streamflow'}
    new_dataset = dsl.api.new_dataset(FEATURE)
    new_datasets = dsl.api.stage_for_download([FEATURE, new_dataset], download_options=download_options)
    try:
        metadata = dsl.api.get_metadata(uris=new_datasets)
        for dataset, metadata in metadata.items():
            assert json.loads(metadata['options']) == download_options
            assert metadata['status'] == 'staged for download'

        # test different download options
        download_options = [{'parameter': 'streamflow'}, {'parameter': 'water_temperature:daily:mean'}]
        dsl.api.stage_for_download(new_datasets, download_options=download_options)
        metadata = dsl.api.get_metadata(uris=new_datasets)
        for i, dataset in enumerate(new_datasets):
            assert json.loads(metadata[dataset]['options']) == download_options[i]
            assert metadata[dataset]['status'] == 'staged for download'
    finally:
        dsl.api.delete(new_datasets)


def test_describe_dataset():
    """Show metadata associated with downloaded dataset.

    This metadata includes as well as the dsl function and kwargs used to
    generate the dataset.

    NOTIMPLEMENTED

    """
    pass
#

def test_open_dataset():
    """Open the dataset as a python/VTK object. Not sure this is needed.

    NOTIMPLEMENTED
    """
    pass


def test_visualize_dataset():
    """Visualize the dataset as a matplotlib/bokeh plot.

    Check for existence of dataset on disk and call appropriate file format
    driver.
    """
    pass


def test_visualize_dataset_options(dataset_save_path):
    """Return visualization available options for dataset."""
    expected = {'type': 'object',
                'properties': {'start': {'default': '2016-01-19 17:00:00',
                                         'type': 'string',
                                         'description': 'start date'
                                         },
                               'end': {'default': '2017-01-18 16:00:00',
                                       'type': 'string',
                                       'description': 'end date'
                                       }
                               },
                'title': 'Timeseries Vizualization Options'
                }
    actual = dsl.api.visualize_dataset_options(DATASET)
    assert actual == expected
