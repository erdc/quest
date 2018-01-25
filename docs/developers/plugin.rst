Writing Quest Service Plugin
============================

Quest is designed to be extensible. It has tree types of plugins: (1) Data Service plugins, (2) Filter plugins, and (3) I/O plugins. Each of them work in a similar way, but this documentation will focus the details of the first type (Data Service plugins). Since there is not a standard interface for accessing the many web services that provide various types of data, the Quest service plugins are used as adapters that translate the specific interface used by each service to a common Quest API for searching, accessing, and downloading data. If we find a new data source that we would like to make accessible through Quest then we need to create a new service plugin for that source.

Data Service Plugins
====================

Services are channels for finding and importing data into Quest. Data services are organized by provider. A provider is composed of one or more services, and all services must be part of a provider. For example, the U.S. Geological Survey (USGS) provides various data products. A subset of these products, say, the National Elevation Datasets (NED) haved been grouped into a ``usgs_ned`` provider. That provider has four different services that provide the various NED data products (i.e. 1 arc second, 1/3 arc second, 1/9 arc second, and Alaska 2 arc second). The process of creating a new Data Service plugin involves subclassing both the ``ProviderBase`` class and the ``ServiceBase`` class. To illustrate this process, we will provide code examples that create an example web service provider (``ExampleProvider``) that contains two services (``ExampleService1`` and ``ExampleService2``).

1. Provider Base Class
----------------------

The `ProviderBase` class acts as the gateway to all of the services that are part of a provider. Most of the code resides in the abstract base class, so subclassing it is very simple, and involves specifying a few attributes. For example::

    from .base import ProviderBase

    class ExampleProvider(ProviderBase):
        service_base_class = None  #TODO: This will be implemented in the next step
        display_name = 'Example Web Provider'
        description = 'Example ProviderBase subclass for Quest'
        organization_name = 'Example Data Provider Organization'
        organization_abbr = 'EDPO'

This is all that is required to subclass the ``ProviderBase``. As you will notice the attribute ``service_base_class`` was left as ``None``. This attribute refers to a base class that is the parent of all of the services that belong to this provider. The ``ProviderBase`` will find all of the subclasses of the class specified by ``service_base_class`` and register them as services of the provider. Therefore the next step is to create a `2. Service Base Class`_.

2. Service Base Class
---------------------

A data service plugin must subclass the ``ServiceBase`` class (or one of it's subclasses, see `Specialized Service Base Subclasses`_) to act as the base class for all services in the plugin. This ``ServiceBase`` subclass is registered in the provider as the `service_base_class` attribute. As an example we will create an ``ExampleServiceBase`` class that subclasses the ``ServiceBase`` class::

    from .base import ProviderBase, ServiceBase

    class ExampleServiceBase(ServiceBase):
        service_name = None
        display_name = None
        description = None
        service_type = None
        unmapped_parameters_available = None
        geom_type = None
        datatype = None
        geographical_areas = None
        bounding_boxes = None
        smtk_template = None
        _parameter_map = None

        def download(self, feature, file_path, dataset, **params):
            pass  #TODO: This will be implemented later

        def get_features(self, **kwargs):
            pass  #TODO: This will be implemented later

    class ExampleProvider(ProviderBase):
       service_base_class = ExampleServiceBase
       ...

.. note::

    The ``ExampleServiceBase`` class needed to be defined above the ``ExampleProvider`` class so we could reference it to assign the ``service_base_class`` attribute in the ``ExampleProvider``.

The content of ``ExampleServiceBase`` has not yet been fully implemented. The above example simply illustrates the structure. All of the attributes and methods shown in the ``ExampleServiceBase`` will need to be implemented either in this class directly or in the services that subclass this base class. The specifics of how this are done will be different for each plugin, but the next step, `3. Service Classes`_ will demonstrate one way to do it.

.. tip::

    Specialized Service Base Subclasses

    There are a couple of special cases that apply to services from various providers. To allow all of these services to use the same codebase a couple of other base classes are available that can be used in place of the ``ServiceBase``.

    TimePeriodServiceBase
    ~~~~~~~~~~~~~~~~~~~~~

    This base class simply adds two parameters, a `start` and `end` date to represent the time period for the data being requested (see `d. Specify the Download Options`_).

    SingleFileServiceBase
    ~~~~~~~~~~~~~~~~~~~~~

    This base class implements the `download` method for services where there is simply a download url that links to a single zip file that contains the data.

3. Service Classes
------------------

After a ``ServiceBase`` subclass has been created (in our example this is the ``ExampleServiceBase``) then the next step is to create classes for each specific service. While the specifics of this step can vary significantly between plugins, the overall structure and process are similar and will be broken down in to several sub-steps:

  * `a. Required Service Class Attributes`_
  * `b. Implement the get_features Method`_
  * `c. Implement the download Method`_
  * `d. Specify the Download Options`_

Continuing the example from above we will create two service classes that each subclass the ``ExampleServiceBase``. We'll first focus on assigning all of the required class attributes.

a. Required Service Class Attributes
....................................

  * ``service_name`` (String): A unique identifier for the service. It should contain only alpha-numeric characters or ``_`` or ``-``. There should be no spaces.
  * ``display_name`` (String): A displayable version of the service name (may contain spaces) for use in GUIs.
  * ``description`` (String): A brief description of the service that will be available in the service's metadata.
  * ``service_type`` (String): A keyword that indicates the type of data that the service provides. Must be one of `geo-discrete`, `geo-seamless` or `geo-typical`.  (# TODO: provide link to description of service types in the docs)
  * ``unmapped_parameters_available`` (Bool): Whether or not additional parameters are available from the service other than those that are listed in the ``_parameter_map``.
  * ``geom_type`` (String): Describes what type of geometry represents the locations of the data (for `geo-discrete` services only). Must be `Point`, `Line`, `Polygon`. Leave as ``None`` for service of type other than `geo-discrete`.
  * ``datatype`` (String): Represents the type of data that is accessible from the service. Must be `timeseries`, `raster`, or `other`.
  * ``geographical_areas`` (List): A list of descriptive words that represent the areas where data is available (e.g. `['North America', 'Europe']`). Should be left as ``None`` for `geo-typical` service types.
  * ``bounding_boxes`` (List): A list of bounding boxes represented as tuples in the form (x-min, y-min, x-max, y-max). For example `[(-180, -90, 180, 90)]`.
  * ``smtk_template`` (String): The name of the SMTK template file that describes the download options for the service.
  * ``_parameter_map`` (Dict): A mapping of parameters as they are called by the service, to the controlled vocabulary parameter names in Quest.

In some cases the attributes will be the same for both services, so they can be assigned in the ``ExampleServiceBase`` class. The rest of the attributes, that are different between the two services, will be assigned in the service classes themselves::

    from .base import ProviderBase, ServiceBase

    class ExampleServiceBase(ServiceBase):
        service_name = None
        display_name = None
        description = None
        service_type = 'geo-discrete'
        unmapped_parameters_available = False
        geom_type = 'Point'
        datatype = 'timeseries'
        geographical_areas = ['Worldwide']
        bounding_boxes = [
            [-180, -90, 180, 90],
        ]
        smtk_template = None

        def get_features(self, **kwargs):
            pass  #TODO: This will be implemented later

        def download(self, feature, file_path, dataset, **params):
            pass  #TODO: This will be implemented later


    class ExampleService1(ExampleServiceBase):
        service_name = 'example-1'
        display_name = 'Example Service 1'
        description = 'First example service'

        _parameter_map = {}


    class ExampleService2(ExampleServiceBase):
        service_name = 'example-2'
        display_name = 'Example Service 2'
        description = 'Second example service'

        _parameter_map = {}

    class ExampleProvider(ProviderBase):
       service_base_class = ExampleServiceBase
       ...

b. Implement the ``get_features`` Method
........................................
The purpose of the ``get_features`` method is to extract key metadata from the service that describes what data is available from that service. For `geo-discrete` services this would include a list of locations where the service has data in addition to other key metadata at each location. The return value for ``get_features`` should be a Pandas DataFrame indexed by a unique id (known as the `service_id`) with the following columns:

 * `display_name`: (will be set to `service_id` if not provided)
 * `description`: (will be set to '' if not provided)
 * `service_id`: a unique id that is used by the web service to identify the data

For `geo-discrete` services the DataFrame must also include a representation of the features' geometry. Any of the following options are valid ways to specify the geometry:

 1) `geometry`: a geojson string or Shapely object
 2) `latitude` and `longitude`: two columns with the decimal degree coordinates of a point
 3) `geometry_type`, `latitudes`, and `longitudes`: `Point`, `Line`, or `Polygon` with a list of coordinates
 4) `bbox`: tuple with order (lon min, lat min, lon max, lat max)

All other fields that the DataFrame contains will be accumulated into a ``dict`` and placed in a column called `metadata`.

Similar to the attributes the ``get_features`` method may be implemented in the service classes (e.g. ``ExampleService1`` and ``ExampleService2``), or in the base class (e.g. ``ExampleServiceBase``), or some combination of both.

c. Implement the ``download`` Method
....................................
The ``download`` method is responsible for retrieving the data from the data source using the specified download options, save it to disk, and then return a dictionary of key metadata. The download method should accept several arguments:

 * `feature`: the service_id for the feature that is associated with the data to be downloaded
 * `file_path`: the path to the directory on disk where Quest expects the data to be written
 * `dataset`: the Quest dataset id associated with the data to be downloaded
 * `**params`: key-word arguments for the dataset options

After downloading the data and saving it to disk, this method should return a dictionary ith the following keys:

 * `metadata`: any metadata that was returned by the data source when it was downloaded in the form of a ``dict``
 * `file_path`: the final file path (including the filename) where the data file was writen
 * `file_format`: the format that the file was written in (to be used to determine which I/O plugin to use to read the file)
 * `datatype`: a string representing the type of data. Must be `timeseries`, `raster`, or `other`.
 * `parameter`: a string representing the parameter of the data
 * `unit`: a string representing the units of the data


d. Specify the Download Options
...............................
Data sources's APIs often allow various options to be specified to determine what data to download, what format it should be in, etc.

The download options that are needed for each service are defined using the Python library `Param (https://ioam.github.io/param/)`_. This library enables parameters to have features like type and range checking, documentation strings, default values, etc. Refer to the `Param documentation (https://ioam.github.io/param/)`_ for more information.


.. todo::

    Describe how `param` is used to define the parameters that are needed to download datasets for each service.






