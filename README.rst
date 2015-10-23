Environmental Simulator Data Services Library
---------------------------------------------

Python API for Data Services Library

Conda Install
=============
Install Anaconda (http://continuum.io/downloads) or Miniconda (http://conda.io/) for your OS

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


Configuration and Directory Structure
=====================================

DSL can be configured in three ways:

  1. Setting Environmental Variables
  2. Passing in a python dictionary to dsl.api.update_settings()
  3. Reading a yaml file with dsl.api.update_settings_from_file()

Any settings that are not set explicitly are given default values

Description of Settings:

======================= ======================================================================= ====================================
Variable Name           Description                                                             Default
----------------------- ----------------------------------------------------------------------- ------------------------------------
DSL_BASE_DIR            Base directory to save dsl data/metadata                                determined by appdirs python package 
DSL_CACHE_DIR           Location to save cached data/metadata                                   DSL_BASE_DIR/cache/
DSL_PROJECT_FILE        Name of project metadata file                                           dsl_project.yml
DSL_PROJECTS_INDEX_FILE Name of projects index file listing available projects and their paths  dsl_projects_index.yml
DSL_CONFIG_FILE         Name of dsl_config file that these settings are saved in                dsl_config.yml
DSL_USER_SERVICES       list of web/file uris to user defined DSL services                      None
======================= ======================================================================= ====================================

You can add any extra settings needed by a plugin here as well using the keyword:arg structure.

Notes:
  - A design goal is that downloaded data is reasonably structured and usable even if you don't use DSL
  - A project is a folder that has some metadata and a set of collections
  - All collections in a project are saved in subdirectories of the main project folder for portability
  - Only one project can be active at a time
  - Other projects can be opened as 'local' web services and features/data 'downloaded' in to the current project
  - Only one dataset (with linear progression of versions) can exist in a (collection,parameter,feature) tuple. i.e. You cannot have two temperature datasets like 2015 Temperature and 2013 Temperature in the same collection+feature. You will either need to copy the feature with a new feature_id or copy to a new collection.
  - Any 'project' can be added as a user defined DSL service (either from a local/network drive or http folder). In that case, the 'project' is equivalent to a 'provider' and each 'collection' is equivalent to a 'service'
  - There will be a way to convert folders of non DSL data into a user defined service by adding a dsl_project.yml to the folder with appropriate metadata. These will be read-only projects.
  - There will be three types of services available (use the service_type filter in dsl.api.get_service() to return a specific list)
        - geo-discrete: These are what we currently use, feature based, features have location info
        - geo-seamless: This is for seamless datasets. There is no get_features function. Instead you pass a geometric feature (bbox, line etc) to the service and the data is extracted and returned (eg. GEBCO Global Bathymetry data)
        - geo-typical: This had features, by the features do not have geometry defined. Will function the same as geo-discrete. Will need to add a tag based search option.


Example Directory Structure::

    /path_to_dsl_base_dir/
        cache/                              # data caches go here
        dsl_config.yml                      # dsl configuration settings
        dsl_projects_index.yml              # list of active projects & their paths. projects do not need to be in this directory
        myproject_1/                        # example project called myproject_1
            dsl_project.yml                 # project metadata
            mycollection_1/                 # example collection inside myproject_1
                dsl_collection.yml          # collection metadata
                features.h5                 # master list of features inside collection, can also be csv, geojson
                temperature/                # folder for all temperature data in mycollection_1
                    feature_1/              #   folder for temperature data at feature_1 (feature_1 coords & metadata are in the master features.h5)
                        66a4e39d            #       temperature datasets at feature_1
                        f974a0c1            #       these are different versions of the same dataset, the last one is the final
                        203a91e3            #       the versioning and applyed filters metadata is tracked in dsl_collection.yml
                    feature_2/
                precipitation/
                    feature_1/
                    feature_3/
                    feature_4/
                adh/
                    feature_5/              # directory containing adh model grid defined by a polygon called feature_5
                    feature_6/              # directory containing adh model grid defined by a polygon called feature_6

    /some_other_location/myproject_2/       # another project listed in dsl_projects_index.yml but not in the DSL_BASE_DIR
        dsl_project.yml
        mycollection_1/
        mycollection_2/

