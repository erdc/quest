Quickstart
==========

Before using Quest you must first activate the quest environment. You can then start a Python console and import quest::

    source activate quest
    (quest) $ python

::

    >>> import quest
    >>> services = quest.api.get_services() #as python dict
    >>> services_json = quest.api.get_services(as_json=True) #as pretty printed json string


Examples
--------

.. toctree::
   :maxdepth: 2

   examples