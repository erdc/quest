DSL Design
==========

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
DSL_CACHE_DIR           Location to save cached data/metadata                                   BASE_DIR/cache/
DSL_PROJECTS_DIR        Default directory to save projects                                      BASE_DIR/projects/
DSL_USER_SERVICES       list of web/file uris to user defined DSL services                      None
======================= ======================================================================= ====================================

You can add any extra settings needed by a plugin here as well using the keyword:arg structure.

Design Goals:
  - Data downloaded through DSL should be reasonably structured, portable and usable even if you don't use DSL later
  - A DSL project (defined below), should be usable as a user defined DSL service from either a folder or http url
  - Be able to easily convert a folder of structured data into a read-only user defined DSL service by adding a few metadata files


Projects and Collections:
  - A project is a folder that has some metadata and a set of collections
  - All collections in a project are saved in subdirectories of the main project folder for portability
  - Only one project can be active at a time, if none is specified a project called 'default' will be created and used
  - Other projects can be opened as 'local' web services and features/data 'downloaded' in to the current project
  - Only one dataset (with linear progression of versions) can exist in a (collection,parameter,feature) tuple. i.e. You cannot have two temperature datasets like 2015 Temperature and 2013 Temperature in the same collection+feature. You will either need to copy the feature with a new feature_id or copy to a new collection.
  - Any 'project' can be added as a user defined DSL service (either from a local/network drive or http folder). In that case, the 'project' is equivalent to a 'provider' and each 'collection' is equivalent to a 'service'
  - There will be a way to convert folders of non DSL data into a user defined service by adding a dsl_project.yml to the folder with appropriate metadata. These will be read-only projects.


Services:
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
                parameters.yml              # file to keep track of available parameters, download status, versions of downloaded data etc
                temperature/                # folder for all temperature data in mycollection_1
                    feature_1/              #   folder for temperature data at feature_1 (feature_1 coords & metadata are in the master features.h5)
                        66a4e39d            #       temperature datasets at feature_1
                        f974a0c1            #       these are different versions of the same dataset, the last one is the final
                        203a91e3            #       the versioning and applied filters metadata is tracked in dsl_collection.yml
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
