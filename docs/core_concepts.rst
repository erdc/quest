Core Concepts
-------------

Quest uses a hierarchical structure to organize and manage datasets, and data sources. The dataset hierarchy begins with `projects` which contains `collections` which contain `features` which have `datasets`. A more detailed description of each level is given below.

Projects
^^^^^^^^

A Quest Project is the base organizing factor. The first time Quest is started a
default project is created. Only one project can be active at a time and
currently the api does not allow copying data from one project to another.

Physically, a project maps to a folder on the computer. All data and metadata
associated with a project is stored under the project folder. The metadata is
stored in a sqlite database.exi

Collections
^^^^^^^^^^^

Collections are a way of organizing data within a project. Collection names are
unique and the collection name maps directly to a folder name in the project folder.

Features
^^^^^^^^

Features are a unique identifiers that indicate a group of datasets. Typically,
these are geospatial locations, i.e., monitoring stations, counties, lakes,
roads at which data exists. Features can also just be a tag or name to group data
that does not have a geospatial component (i.e. geotypical datasets). Features
are always either part of a collection or part of a web service.

Datasets
^^^^^^^^

These are the actual individual data files or in some cases a folder of data.
Datasets are always located at a feature. Currently a dataset can only be
attached to a single feature by design.

____

Data sources are organized into `providers` which contain one or more `services.

Providers
~~~~~~~~~

Data providers are the top level source of data. Providers are composed of one or more `Services`_, and typically represent an organization or specific part of an organization that provides data. In Quest Providers are a way of grouping related services.

Services
^^^^^^^^

A data service is a specific type or channel of data that is offered from a `Provider`_, and are the primary means of ingesting data into Quest.
