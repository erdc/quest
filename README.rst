Environmental Simulator Data Services Library
---------------------------------------------

Python API for Data Services Library

Conda Install
=============
Install Anaconda (http://continuum.io/downloads) or Miniconda (http://conda.io/) for your OS

conda config --add channels erdc
conda config --add channels ulmo
conda config --add channels ioos
conda env create -n dsl --file conda-requirements.yml
source activate dsl (just activate dsl on windows)
pip install -r requirements.txt


Regular Installation
====================

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