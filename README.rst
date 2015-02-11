Environmental Simulator Data Services Library
---------------------------------------------

Python API for Data Services Library

Installation
============

from the base directory type:

`pip install -r requirements.txt`

This will download to correct feature/raster branch of ulmo and install all dsl 
dependencies into your python path.

Note: `python setup.py install` and `python setup.py develop` have issues installing 
numpy correctly on osx.

Usage Examples
==============

>>> import dsl
>>> services = dsl.api.get_services() #as python dict
>>> services_json = dsl.api.get_services(as_json=True) #as pretty printed json string