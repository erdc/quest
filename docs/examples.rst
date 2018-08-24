Quest Examples
==============

.. toctree::
   :maxdepth: 2

   examples


Project Management
------------------

::

   In [1]: from quest import api

   In [2]: api.get_active_project()
   Out[2]: 'default'

   In [3]: api.get_projects()
   Out[3]: ['default']

   In [4]: api.new_project('my_proj')
   Out[4]:
   {'created_at': datetime.datetime(2017, 10, 13, 15, 1, 42, 322881),
    'description': '',
    'display_name': 'my_proj',
    'metadata': {},
    'updated_at': None}

   In [5]: api.get_projects()
   Out[5]: ['my_proj', 'default']

   In [6]: api.set_active_project('my_proj')
   Out[6]: 'my_proj'

   In [7]: api.get_active_project()
   Out[7]: 'my_proj'

   In [8]: api.delete_project('my_proj')
   Out[8]: {'default': {'folder': 'default'}}

   In [9]: api.get_active_project()
   Out[9]: 'default'


Collection Management
---------------------

::

   In [1]: from quest import api

   In [2]: api.get_collections()
   Out[2]: []

   In [3]: api.new_collection('demo')
   Out[3]:
   {'created_at': datetime.datetime(2017, 10, 13, 15, 5, 33, 385739),
    'description': '',
    'display_name': 'demo',
    'metadata': {},
    'name': 'demo',
    'updated_at': None}

   In [4]: api.get_collections()
   Out[4]: ['demo']

   In [5]: api.delete('demo')
   Out[5]: True

   In [6]: api.get_collections()
   Out[6]: []

Download USGS Streamflow Data
-----------------------------

::

   In [1]: from quest import api

   In [2]: service = 'svc://usgs-nwis:iv'

   In [3]: bbox = -91.2169473497967, 32.1042768209676, -90.38047319857966, 32.60480883953886

   In [4]: parameter = 'streamflow'

   In [5]: service_features = api.get_features(service, filters={'bbox': bbox, 'parameter': parameter})

   In [6]: service_features
   Out[6]: ['svc://usgs-nwis:iv/07289000', 'svc://usgs-nwis:iv/07290000']

   In [7]: api.new_collection('demo')
   Out[7]:
   {'created_at': datetime.datetime(2017, 10, 13, 16, 1, 20, 665131),
    'description': '',
    'display_name': 'demo',
    'metadata': {},
    'name': 'demo',
    'updated_at': None}

   In [8]: collection_features = api.add_features('demo', service_features)

   In [9]: collection_features
   Out[9]: ['fa2e58257ec04d4cb0f18feec51df736', 'fb8d012eb816477b830643369ef7220e']

   In [10]: api.download_options(service)
   Out[10]:
   {'svc://usgs-nwis:iv': {'properties': {'end': {'description': 'end date',
       'type': 'string'},
      'parameter': {'description': 'parameter',
       'enum': ['gage_height', 'streamflow', 'water_temperature'],
       'type': 'string'},
      'period': {'description': 'period date', 'type': 'string'},
      'start': {'description': 'start date', 'type': 'string'}},
     'title': 'USGS NWIS Download Options',
     'type': 'object'}}

   In [11]: options = {'parameter': parameter, 'start': '2016-10-01', 'end': '2017-09-30'}

   In [12]: datasets = api.stage_for_download(collection_features, options=options)

   In [13]: datasets
   Out[13]: ['d70123cb1ad944a988f64f449a7d8e8e', 'd5a964398a074ae7b8183e8817c4b882']

   In [14]: api.download_datasets(datasets)
   Out[14]:
   {'d5a964398a074ae7b8183e8817c4b882': 'downloaded',
    'd70123cb1ad944a988f64f449a7d8e8e': 'downloaded'}

   In [15]: api.get_datasets(expand=True)
   Out[15]:
   {'d5a964398a074ae7b8183e8817c4b882': {'collection': 'demo',
     'created_at': Timestamp('2017-10-13 16:01:20.665627'),
     'datatype': 'timeseries',
     'description': None,
     'display_name': 'd5a964398a074ae7b8183e8817c4b882',
     'feature': 'fb8d012eb816477b830643369ef7220e',
     'file_format': 'timeseries-hdf5',
     'file_path': '/path/to/quest/projects/default/demo/usgs-nwis/iv/d5a964398a074ae7b8183e8817c4b882/d5a964398a074ae7b8183e8817c4b882.h5',
     'message': 'success',
     'metadata': {'last_refresh': '2017-10-13T16:04:13',
      'methods': {'80265': {'id': '80265'}},
      'qualifiers': {'0': {'code': 'A',
        'description': 'Approved for publication -- Processing and review completed.',
        'id': '0',
        'network': 'NWIS',
        'vocabulary': 'uv_rmk_cd'},
       '1': {'code': 'P',
        'description': 'Provisional data subject to revision.',
        'id': '1',
        'network': 'NWIS',
        'vocabulary': 'uv_rmk_cd'}},
      'site': {'agency': 'USGS',
       'code': '07290000',
       'county': '28049',
       'huc': '08060202',
       'location': {'latitude': '32.34777778',
        'longitude': '-90.6969444',
        'srs': 'EPSG:4326'},
       'name': 'BIG BLACK RIVER NR BOVINA, MS',
       'network': 'NWIS',
       'site_type': 'ST',
       'state_code': '28',
       'timezone_info': {'default_tz': {'abbreviation': 'CST',
         'offset': '-06:00'},
        'dst_tz': {'abbreviation': 'CDT', 'offset': '-05:00'},
        'uses_dst': True}},
      'variable': {'code': '00060',
       'description': 'Discharge, cubic feet per second',
       'id': '45807197',
       'name': 'Streamflow, ft&#179;/s',
       'network': 'NWIS',
       'no_data_value': '-999999.0',
       'statistic': {'code': '00000', 'name': None},
       'units': {'code': 'ft3/s'},
       'value_type': 'Derived Value',
       'variable_oid': '45807197',
       'vocabulary': 'NWIS:UnitValues'}},
     'name': 'd5a964398a074ae7b8183e8817c4b882',
     'options': {'end': '2017-09-30',
      'parameter': 'streamflow',
      'start': '2016-10-01'},
     'parameter': 'streamflow',
     'source': 'download',
     'status': 'downloaded',
     'unit': 'ft3/s',
     'updated_at': None,
     'visualization_path': ''},
    'd70123cb1ad944a988f64f449a7d8e8e': {'collection': 'demo',
     'created_at': Timestamp('2017-10-13 16:01:20.665627'),
     'datatype': 'timeseries',
     'description': None,
     'display_name': 'd70123cb1ad944a988f64f449a7d8e8e',
     'feature': 'fa2e58257ec04d4cb0f18feec51df736',
     'file_format': 'timeseries-hdf5',
     'file_path': '/path/to/quest/projects/default/demo/usgs-nwis/iv/d70123cb1ad944a988f64f449a7d8e8e/d70123cb1ad944a988f64f449a7d8e8e.h5',
     'message': 'success',
     'metadata': {'last_refresh': '2017-10-13T16:04:27',
      'methods': {'80244': {'id': '80244'}},
      'qualifiers': {'0': {'code': 'e',
        'description': 'Value has been edited or estimated by USGS personnel and is write protected.',
        'id': '0',
        'network': 'NWIS',
        'vocabulary': 'uv_rmk_cd'},
       '1': {'code': 'A',
        'description': 'Approved for publication -- Processing and review completed.',
        'id': '1',
        'network': 'NWIS',
        'vocabulary': 'uv_rmk_cd'},
       '2': {'code': 'P',
        'description': 'Provisional data subject to revision.',
        'id': '2',
        'network': 'NWIS',
        'vocabulary': 'uv_rmk_cd'}},
      'site': {'agency': 'USGS',
       'code': '07289000',
       'county': '28149',
       'huc': '08060100',
       'location': {'latitude': '32.315',
        'longitude': '-90.9058333',
        'srs': 'EPSG:4326'},
       'name': 'MISSISSIPPI RIVER AT VICKSBURG, MS',
       'network': 'NWIS',
       'site_type': 'ST',
       'state_code': '28',
       'timezone_info': {'default_tz': {'abbreviation': 'CST',
         'offset': '-06:00'},
        'dst_tz': {'abbreviation': 'CDT', 'offset': '-05:00'},
        'uses_dst': True}},
      'variable': {'code': '00060',
       'description': 'Discharge, cubic feet per second',
       'id': '45807197',
       'name': 'Streamflow, ft&#179;/s',
       'network': 'NWIS',
       'no_data_value': '-999999.0',
       'statistic': {'code': '00000', 'name': None},
       'units': {'code': 'ft3/s'},
       'value_type': 'Derived Value',
       'variable_oid': '45807197',
       'vocabulary': 'NWIS:UnitValues'}},
     'name': 'd70123cb1ad944a988f64f449a7d8e8e',
     'options': {'end': '2017-09-30',
      'parameter': 'streamflow',
      'start': '2016-10-01'},
     'parameter': 'streamflow',
     'source': 'download',
     'status': 'downloaded',
     'unit': 'ft3/s',
     'updated_at': None,
     'visualization_path': ''}}


Applying Tools
----------------

Continuing from previous example.

::

   In [16]: dataset = datasets[0]

   In [17]: api.get_tools(filters={'dataset': dataset})
   Out[17]: ['ts-flow-duration', 'ts-resample', 'ts-unit-conversion', 'ts-remove-outliers']

   In [18]: filter_name = 'ts-resample'

   In [19]: api.apply_filter_options(filter_name)
   Out[19]:
   {'properties': {'method': {'description': 'resample method',
      'type': {'default': 'mean',
       'enum': ['sum', 'mean', 'std', 'max', 'min', 'median']}},
     'period': {'description': 'resample frequency',
      'type': {'default': 'daily',
       'enum': ['daily', 'weekly', 'monthly', 'annual']}}},
    'required': ['period', 'method'],
    'title': 'Resample Timeseries Filter',
    'type': 'object'}

   In [20]: options = {'method': 'max', 'period': 'daily'}

   In [21]: api.run_filter(filter_name, datasets=dataset, options=options)
   Out[21]: {'datasets': ['db98e371e7a64a02a773004c6ddc90ff'], 'features': []}

   In [22]: api.get_metadata('db98e371e7a64a02a773004c6ddc90ff')
   Out[22]:
   {'db98e371e7a64a02a773004c6ddc90ff': {'collection': 'demo',
     'created_at': Timestamp('2017-10-13 16:01:20.665627'),
     'datatype': 'timeseries',
     'description': 'TS Filter Applied',
     'display_name': 'db98e371e7a64a02a773004c6ddc90ff',
     'feature': 'fa2e58257ec04d4cb0f18feec51df736',
     'file_format': 'timeseries-hdf5',
     'file_path': '/path/to/quest/projects/default/demo/usgs-nwis/iv/d70123cb1ad944a988f64f449a7d8e8e/db98e371e7a64a02a773004c6ddc90ff',
     'message': 'TS Filter Applied',
     'metadata': {},
     'name': 'db98e371e7a64a02a773004c6ddc90ff',
     'options': {'dataset': ['d70123cb1ad944a988f64f449a7d8e8e'],
      'features': None,
      'filter_applied': 'ts-resample',
      'filter_options': {'method': 'max', 'period': 'daily'}},
     'parameter': 'streamflow:daily:max',
     'source': 'derived',
     'status': 'filter applied',
     'unit': 'ft3/s',
     'updated_at': None,
     'visualization_path': ''}}
