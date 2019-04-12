Quickstart
==========

Before using Quest you must first activate the quest environment. You can then start a IPython console and import quest:

.. code-block:: bash

    conda activate quest
    (quest) $ ipython

.. code-block:: python

    In [1]: import quest

The simplest way to download some data is to use the :func:`quest.api.get_data` call.

.. code-block:: python

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


Quest can download many different types of data from various data providers. In this example we've downloaded timeseries streamflow data from the `USGS National Water Information System (NWIS) <https://waterdata.usgs.gov/nwis>`_. This type of data is returned as a :obj:`pandas.DataFrame` (see `Pandas Documentation <https://pandas.pydata.org/index.html>`_).

For other examples of how Quest can be used refer to our `Jupyter Notebooks <https://github.com/erdc/quest/tree/master/examples/notebooks>`_ or review the examples listed below.

Examples
--------

.. toctree::
  :maxdepth: 2

  examples/slowstart
  examples/index

