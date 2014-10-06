Environmental Simulator Data Services Library
---------------------------------------------

Currently a stub implementation of API

Installation
============

from the root dir type:

python setup.py install

OR

python setup.py develop

for development mode

Usage Examples
==============

>>> import data_services as dsl
>>> services = dsl.api.get_sources() #as python dict
>>> services_json = dsl.api.get_sources(as_json=True) #as pretty printed json string

Python API Description
======================

High level description of python API to data services library.

Available Operations (Work in Progress):

* List (query for) data sources:
  Args: Config File/All
  Return: JSON w/ metadata (Point/Line/Poly; Type of Data (Hydro/Met/etc); Source)

* Get locations(point, lines, polygons):
  Args: Sources, Parameters, Time, bb, polygon
  Return: GeoJson + metadata.

* Get data:
  Args: Source, Sites, Parameters, Time, Other filters, subsample
  Return: dict(type: data)

* Get Subsampled Data:
  Args: subsample, Call get_data

* Add/Edit/Delete Data Source (with type, metadata etc) -- ie change the config file.

* Query for filters:
  Arg: source type
  returns list of filters: Band Pass, Unit Conversion, Interpolant etc.

* Get filter:
  Arg: Filter
  Returns: Filter args

* Apply Filter:
  Arg: Filter, Filter Args
  Returns: new field.
