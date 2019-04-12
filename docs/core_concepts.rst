Core Concepts
=============

Quest is a python library designed to automate the following data management tasks:

    * Discovery
    * Retrieval
    * Organization
    * Transformation
    * Archival


At the heart of all of these tasks are `datasets`_. Each of the tasks listed above involves finding, getting, storing, changing, or sharing a ``dataset``. The underlying concepts for how Quest accomplishes these five tasks will be described below and are grouped into the following three sections:

    * `Local Data Organization`_
    * `Data Transformations`_
    * `Data Repositories`_

        * Discovery
        * Retrieval
        * Archival

.. _core-concepts-data-organization:

Local Data Organization
-----------------------

Quest uses a hierarchical structure to organize and manage datasets, and data sources. The dataset hierarchy begins with `projects`_ which contains `collections`_ which have `datasets`_. A more detailed description of each level is given below.

.. _core-concepts-projects:

Projects
^^^^^^^^

A Quest Project is the base organizing factor. The first time Quest is started a
default project is created. Only one project can be active at a time and
currently the api does not allow copying data from one project to another.

Physically, a project maps to a folder on the computer. All data and metadata
associated with a project is stored under the project folder. The metadata is
stored in a sqlite database.

.. _core-concepts-collections:

Collections
^^^^^^^^^^^

Collections are a way of organizing data within a project. Collection names are
unique and the collection name maps directly to a folder name in the project folder.

.. _core-concepts-datasets:

Datasets
^^^^^^^^

These are the actual individual data files or in some cases a folder of data. Datasets have associated metadata that is stored in the project directory.

.. _core-concepts-data-transformations:

Data Transformations
--------------------

Quest facilitates transforming data through the use of `tools`_. Some examples of the kinds of transformations that Quest can do include merging datasets, aggregating data within a dataset, or changing the format that the data is stored in.

.. _core-concepts-tools:

Tools
^^^^^
Quest ``tools`` are a way to perform some kind of operation on data. It is important to note that a ``tool`` will never perform "in-place" changes the datasets that it operates on. This means that datasets that are passed to a ``tool`` will remain unchanged, and the ``tool`` will create new datasets that have the transformed data. New ``tools`` can be added to Quest through :ref:`tool-plugins`.

Tools define a set of options that a user must specify when using the tool.

.. _core-concepts-data-repositories:

Data Repositories
-----------------

When Quest is used to search for data it searches among all of the data repositories or data `providers`_ that are registered with Quest. Similar to `Tools`_ `Providers`_ are added to Quest as plugins (see :ref:`provider-plugins`). `Providers`_ contain one or more `services`_. `Services`_ provide an interface for a single data product. Each service has a :ref:`core-concepts-catalogs`, which stores metadata about the datasets that are available from that service and is what enables Quest to search for data.

.. _core-concepts-providers:

Providers
^^^^^^^^^

Data `providers` are the top level source of data. Providers are composed of one or more `Services`_, and typically represent an organization or specific part of an organization that provides data. In Quest, `providers` are a way of grouping related services.

.. _core-concepts-services:

Services
^^^^^^^^

A data service is a specific type or channel of data that is offered from a `Providers`_, and are the primary means of ingesting data into Quest.

.. _core-concepts-catalogs:

Catalogs
^^^^^^^^

.. _core-concepts-catalog-entries:

Catalog Entries
^^^^^^^^^^^^^^^

Catalog Entries are a unique identifiers that indicate a group of datasets. Typically,
these are geospatial locations, i.e., monitoring stations, counties, lakes,
roads at which data exists. Features can also just be a tag or name to group data
that does not have a geospatial component (i.e. geotypical datasets). Features
are always either part of a collection or part of a web service.