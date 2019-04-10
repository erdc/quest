Slow Start: A step by step breakdown of the Quickstart example
==============================================================

The quickstart example demonstrated the fastest way to download and start working with data using Quest:

.. code-block:: python

    In [1]: import quest

    In [2]: data = quest.api.get_data(
       ...:     collection_name='quick-start',
       ...:     service_uri='svc://usgs-nwis:iv',
       ...:     search_filters={'bbox': [-91, 32.25, -90.8, 32.4]},
       ...:     download_options={'parameter': 'streamflow'},
       ...: )[0]

    In [3]: data.head()
    Out[3]:
                        qualifiers  streamflow
    datetime
    2018-04-03 16:00:00          P   1180000.0
    2018-04-03 17:00:00          P   1180000.0
    2018-04-03 18:00:00          P   1180000.0
    2018-04-03 19:00:00          P   1180000.0
    2018-04-03 20:00:00          P   1180000.0

There is a lot going on in this seemingly simple example, so we're going to break it down and explain every step.

The first thing to note is that the function :func:`quest.api.get_data`, is a workflow function, or in other words a
function that calls several other functions in succession. This provides a convenient way to get your data in one step
when you already know all of inputs you need. You can also use Quest to do the same workflow in a more interactive way.
The :func:`quest.api.get_data` call performs the following steps behind the scenes:

  1. :ref:`create-collection`
  2. :ref:`select-service`
  3. :ref:`search-catalog`
  4. :ref:`add-datasets`
  5. :ref:`download-data`
  6. :ref:`open-data`

The following sections will explain each of these steps in detail.

.. _create-collection:

Create a Collection
-------------------

When Quest downloads data it needs to know where to put them. To keep data organized Quest provides a local organization
hierarchy to manage data (see :ref:`core-concepts-data-organization`). At the top of the hierarchy is a :term:`project`, and all Quest calls
will always apply to whatever project is active. For more details about managing projects see (:ref:`examples-manage-projects`).
Within :term:`projects` are :term:`collections` . All data that are downloaded by Quest are put in a :term:`collection` . In the
:func:`quest.api.get_data` example above the ``collection_name`` argument specifies which :term:`collection` to put the data
in. If there isn't already a :term:`collection` with the name specified by the ``collection_name`` argument then ``get_data``
function will create it.

This process can also be done manually. Using the Quest API we can get a list of the collections with the
:func:`quest.api.get_collection` function:

.. code-block:: python

  In [4]: quest.api.get_collections()
  Out[4]: ['quick-start']

As you can see there currently is only one collection called "quick-start" that was created as a result of the ``get_data``
call made previously.  To create a new collection we manually we can use the :func:`quest.api.new_collection` function:

.. code-block:: python

  In [5]: quest.api.new_collection('slow-start')
  Out[5]:
  {'name': 'slow-start',
   'display_name': 'slow-start',
   'description': '',
   'created_at': datetime.datetime(2019, 4, 4, 13, 43, 14, 823227),
   'updated_at': None,
   'metadata': {}}

This function returns the metadata that is associated with this newly created collection. For more details about working
with collection see :ref:`examples-manage-collections`.

.. _select-service:

Select a Data Service
---------------------

Once we have a place to store data locally we need to decide what data we want to download. Quest provides the ability
to search for data among many different data sources, or :term:`providers`. Each :term:`provider` will offer one or more data
:term:`services` (see :ref:`core-concepts-data-repositories`). We can list the available :term:`services` by calling
:func:`quest.api.get_services`:

.. code-block:: python

  In [6]: quest.api.get_services()
  Out[6]:
  ['svc://cuahsi-hydroshare:hs_geo',
   'svc://cuahsi-hydroshare:hs_norm',
   'svc://noaa-coast:coops-meteorological',
   'svc://noaa-coast:coops-water',
   'svc://noaa-coast:ndbc',
   'svc://noaa-ncdc:ghcn-daily',
   'svc://noaa-ncdc:gsod',
   'svc://quest:quest',
   'svc://usgs-ned:1-arc-second',
   'svc://usgs-ned:13-arc-second',
   'svc://usgs-ned:19-arc-second',
   'svc://usgs-ned:alaska-2-arc-second',
   'svc://usgs-nlcd:2001',
   'svc://usgs-nlcd:2006',
   'svc://usgs-nlcd:2011',
   'svc://usgs-nwis:dv',
   'svc://usgs-nwis:iv',
   'svc://wmts:seamless_imagery']

Each :term:`service` is represented by a service URI. In our quickstart example we used the penultimate service URI listed
here: 'svc://usgs-nwis:iv'. This service URI is needed to tell Quest where to search for data.

.. _search-catalog:

Search for Datasets
-------------------

Each :term:`service` has a :term:`catalog` or listing of the data it provides. To search for data we need to tell Quest which
service's or services' catalog to search. To limit our search we can pass in a dictionary of key-value pairs that specify
filter criteria to filter the catalog entries by. In the quickstart example we filtered the catalog using a bounding box.

.. code-block:: python

  ...:     search_filters={'bbox': [-91, 32.25, -90.8, 32.4]},

To manually search the catalog we can call the Quest API function :func:`quest.api.search_catalog` and pass it the
service URI and the filters dictionary:

.. code-block:: python

  In [7]: quest.api.search_catalog(uris='svc://usgs-nwis:iv', filters={'bbox': [-91, 32.25, -90.8, 32.4]})
  Out[7]: ['svc://usgs-nwis:iv/07289000']

The return value from :func:`quest.api.search_catalog` is a list of :term:`catalog entry` URIs. The :term:`catalog entry` URI
looks just like the :term:`service` URI that it came from with an appended catalog ID number. This :term:`catalog entry` URI is
used to download the data associated to that :term:`catalog entry`.

.. _add-datasets:

Add Datasets to Collection
--------------------------

Before we can download the data associated with a :term:`catalog entry` we need to create a :term:`dataset` derived from that
:term:`catalog entry`. A Quest :term:`dataset` represents a piece of data and stores all of the metadata associated with those
data. Every Quest :term:`dataset` has an associated :term:`catalog entry` that links it back to the :term:`service` where the data
came from, and an associated :term:`collection` that acts as a container for the data. We can create new :term:`datasets` by
calling :func:`quest.api.add_datasets` and passing it both the `collection` and the :term:`catalog entry` or entries from
which to create the :term:`datasets`.

.. code-block:: python

  In [8]: quest.api.add_datasets('slow-start', 'svc://usgs-nwis:iv/07289000')
  Out[8: ['d0b2baa58434445fb2d1fee0330d5acf']

The return value is a list of dataset IDs from the newly created datasets (in this case it's just a list of one ID. We
can now use this dataset ID to download the data associated with it.


.. _download-data:

Download Datasets
-----------------

To download data using Quest we use the :func:`quest.api.download_datasets` function. We need to pass it the :term:`dataset`
IDs for the data that we want to download. We also need to pass it a dictionary of download options. Each service specifies
it's own set of download options. To figure out what the download options are for a particular dataset we can either
refer to the documentation for that dataset's service or we can call :func:`quest.api.get_download_options` and pass it
can pass in either the :term:`service` URI the :term:`catalog entry` URI, or the :term:`dataset` ID.

.. code-block:: python

  In [9]: quest.api.get_download_options('d0b2baa58434445fb2d1fee0330d5acf')
  Out[9]:
  {'svc://usgs-nwis:iv/07289000': {'title': 'NWIS Instantaneous Values Service Download Options',
    'properties': [{'name': 'parameter',
      'type': 'ObjectSelector',
      'description': 'parameter',
      'default': None,
      'range': [['gage_height', 'gage_height'],
       ['streamflow', 'streamflow'],
       ['water_temperature', 'water_temperature']]},
     {'name': 'start',
      'type': 'Date',
      'description': 'start date',
      'default': None,
      'bounds': None},
     {'name': 'end',
      'type': 'Date',
      'description': 'end date',
      'default': None,
      'bounds': None},
     {'name': 'period',
      'type': 'String',
      'description': 'time period (e.g. P365D = 365 days or P4W = 4 weeks)',
      'default': 'P365D'}]}}

This returns a dictionary keyed by the URIs that were passed to the fucntion. For each URI key the value is a dictionary
specifying the download options or `properties` for that URI. In this case the download options we can specify are:

  * `parameter`: one of 'gage_height', 'streamflow', or 'water_temperature'
  * `start`: the start date for the period of data want
  * `end`: the end date for the period of data you want
  * `period`: a string representing a period of data you want

Here either the start and end date can be specified or a period string can be specified. If neither are specified then
the default period 'P365D' (meaning a period of 365 days ending with today) will be used by default. In the quickstart
example we specified that we were interested in 'streamflow' data and we didn't specify a period so by default we got
the past year of data. We can do the same here by calling :func:`quest.api.download_datasets`:

.. code-block:: python

  In [10]: quest.api.download_datasets(
      ...:     datasets='d0b2baa58434445fb2d1fee0330d5acf',
      ...:     options={'parameter': 'streamflow'},
      ...: )
  Out[10]: {'d0b2baa58434445fb2d1fee0330d5acf': 'downloaded'}

The return value is a dictionary keyed by the dataset IDs that were passed in where the value is the status. In this case
'downloaded' means that the data associated with the dataset were successfully downloaded.

.. _open-data:

Open Datasets
-------------

When the data associated with a :term:`dataset` are downloaded they are by default stored on disk. Quest can be used to
transform, visualize, or publish the data and will only require the :term:`dataset` ID as an argument. If you'd like to use
other Python tools to work with your data you can use Quest to open your data and read it into a Python data structure.
The data that we downloaded are a timeseries of streamflow values. The default data structure that Quest uses for this
type of data is a :obj:`pandas.DataFrame`. Therefore, when we call :func:`quest.api.open_dataset` we will getback our
data in a DataFrame.

.. code-block:: python

  In [6]: data = quest.api.open_dataset('d0b2baa58434445fb2d1fee0330d5acf')

  In [7]: data.head()
  Out[7]:
                      qualifiers  streamflow
    datetime
    2018-04-03 16:00:00          P   1180000.0
    2018-04-03 17:00:00          P   1180000.0
    2018-04-03 18:00:00          P   1180000.0
    2018-04-03 19:00:00          P   1180000.0
    2018-04-03 20:00:00          P   1180000.0

Where to Go from Here
---------------------

