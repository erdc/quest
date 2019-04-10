Quest Examples
==============

.. toctree::
   :maxdepth: 2

   slowstart

.. _examples-manage-projects:

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


.. _examples-manage-collections:

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

.. _examples-running-tools:

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
