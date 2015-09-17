"""API functions related to Collections

"""
from __future__ import print_function
from .. import util
import os
import shutil
import yaml

COLLECTION_METADATA_FILE = 'dsl.yml'

@util.jsonify
def get_collections(filters=None):
    """Get list of available collections.

    Collections are folders on the local disk that contain downloaded or created data
    along with associated metadata.

    Returns
    -------
    collections : dict,
        A python dict representation of the list of available collections 
    """
    return _load_collections()


@util.jsonify     
def new_collection(metadata={}, path=None):
    """Create a new collection

    Create a new collection by creating a new folder and placing a json
    file in the folder for dsl metadata and adding a reference to the 
    master collections metadata folder.

    Parameters
    ----------
    name : str,
        The name of the collection
    metadata : ``dict`` containing optional metadata values
    path: ``None`` or str,
        If ``None`` use default dsl location for collections otherwise use specified path. 

    Returns
    -------
    collection : dict,
        A python dict representation of the collection in the format {uid: metadata}
    """

    uid = util.uid()
    if path is None:
        metadata.update({'path': uid})
        path = util.get_data_dir()
    else:
        metadata.update({'path': os.path.join(path, uid)})

    if metadata.get('display_name') is None:
        metadata['display_name'] = uid

    collection_path = os.path.join(path, uid)
    util.mkdir_if_doesnt_exist(collection_path)

    collection = {uid: metadata}
    collections = _load_collections()
    collections.update(collection)
    _write_collections(collections)

    return collection


@util.jsonify
def update_collection(uid, metadata):
    """Update metadata of collection.
    """
    collections = _load_collections()

    if uid not in list(collections.keys()):
        print('Collection not found')
        return {}

    collections[uid].update(metadata)
    _write_collections(collections)
    return collections[uid]


@util.jsonify
def delete_collection(uid, delete_data=True):
    """delete a collection

    Deletes a collection from the collections metadata file.
    Optionally deletes all data under collection.

    Parameters
    ----------
    name : str,
        The name of the collection

    delete_data : bool,
        if True all data in the collection will be deleted

    Returns
    -------
    collections : dict,
        A python dict representation of the list of available collections, 
        the updated collections list is also written to a json file.
    """
    collections = _load_collections()

    if uid not in list(collections.keys()):
        print('Collection not found')
        return collections

    if delete_data:
        path = collections[uid]['path']
        if os.path.exists(path):
            print('deleting all data under path:', path)
            shutil.rmtree(path)

    print('removing %s from collections' % uid)
    del collections[uid]
    _write_collections(collections)
    return collections


def _load_collections():
    """load list of collections

    """
    path = util.get_collections_index()

    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return yaml.safe_load(f)


def _write_collections(collections):
    """write list of collections to json file 
    """
    path = util.get_collections_index()
    with open(path, 'w') as f:
        yaml.dump(collections, f)


# @util.jsonify
# def add_to_collection(name, service, locations, parameters=None, **kwargs):
#     """adds locations from a service to a collection

#     Note: Data is not downloaded in this function call. Placeholders
#     are placed in the collection. To download data call function
#     download_in_collection

#     Parameters
#     ----------
#     name : str,
#         The name of the collection 
#     service : str,
#         The name of the service
#     locations : str,
#         comma separated list of locations. These are location codes or ids 
#         of the locations to be added from a service
#     parameters : ``None`` or str,
#         comma separated list of parameters to download for each location. If 
#         ``None`` (default) is passed then all available parameters for that 
#         service will be used.

#     Returns
#     -------
#     collection : dict, 
#         A python dict representation of the collection, the collection is also 
#         written to a json file.
#     """

#     if isinstance(locations, dict):
#         features = locations
#         locations = [loc['id'] for loc in features['features']]
#     else:
#         locations = util.listify(locations)
#         features = get_locations(service, locations)

#     parameters = util.listify(parameters)
#     if parameters is None:
#         parameters = get_parameters(service)

#     collection = get_collection(name)
    
#     if 'datasets' not in collection.keys():
#         collection['datasets'] = {}

#     if service not in collection['datasets'].keys():
#         collection['datasets'][service] = {'data': {}, 'locations':{} }

#     dataset = collection['datasets'][service]


#     dataset['locations'] = util.append_features(dataset['locations'], features)

#     for loc, feature in zip(locations, features['features']):
#         if loc in dataset['data'].keys():
#             parameters = list(set(parameters) - set(dataset['data'][loc].keys()))
#         else:
#             dataset['data'][loc] = {}

#         relative_path = feature['properties'].get('relative_path') #required for adding locally generated datasets from filters
#         datatype = feature['properties'].get('datatype')
#         view = feature['properties'].get('view')
#         dataset['data'][loc].update(
#             {p:{
#                 'relative_path': relative_path, 
#                 'datatype': datatype,
#                 'view': view,
#                 } for p in parameters
#             }
#         )
    
#     _write_collection(collection)
#     return collection


# @util.jsonify
# def download_in_collection(name, service=None, location=None, parameter=None, **kwargs):
#     """download data for services/locations/parameters present in collection

#     Currently *all* datasets present in a collection will be downloaded with 
#     default download options. The data is downloaded to subfolders in the 
#     collection folder and a relative path reference is placed in the collection
#     metadata. A separate file is saved for each service/location/parameter tuple.

#     Parameters
#     ----------
#     name : str,
#         The name of the collection

#     Returns
#     -------
#     collection : dict, 
#         A python dict representation of the collection, the collection is also 
#         written to a json file.

#     """
#     collection = get_collection(name)

#     if not any([service, location, parameter]):
#         for service, dataset in collection['datasets'].iteritems():
#             datatype = get_services(names=service)[0].get('datatype')
#             for location, parameters in dataset['data'].iteritems():
#                 path = collection['path']
#                 data_files = get_data(service, location, path=path, parameters=','.join(parameters.keys()))
#                 for parameter, v in data_files[location].iteritems():
#                     if v is None:
#                         msg = "Warning: No data available for (service: %s, location: %s, parameter: %s)" % (service, location, parameter)
#                         warnings.warn(msg)
#                     else:
#                         parameters[parameter]['relative_path'] = os.path.relpath(v, path)
#                         dataset['data'][location][parameter]['datatype'] = datatype
#     else:
#         dataset = collection['datasets'][service]['data']
#         path = collection['path']
#         data_file = get_data(service, location, path=path, parameters=parameter, **kwargs)
#         datatype = get_services(names=service)[0].get('datatype')
#         data_path = data_file[location].get(parameter)
#         if data_path is None:
#             msg = "Warning: No data available for (service: %s, location: %s, parameter: %s)" % (service, location, parameter)
#             warnings.warn(msg)
#         else:
#             dataset[location][parameter]['relative_path'] = os.path.relpath(data_path, path)
#             dataset[location][parameter]['datatype'] = datatype

#     _write_collection(collection)
#     return collection


# @util.jsonify
# def download_in_collection_options(name, service=None, location=None, parameter=None):
#     collection = get_collection(name)

#     options = {}
#     if not any([service, location, parameter]):
#         for service, dataset in collection['datasets'].iteritems():
#             options[service] = {}
#             for location, parameters in dataset['data'].iteritems():
#                 options[service][location] = {}
#                 for parameter in parameters:
#                     print service, location, parameter
#                     options[service][location][parameter] = get_data_options(service, locations=location, parameters=parameter)
#     else:
#         options[service] = {}
#         options[service][location] = {}
#         options[service][location][parameter] = get_data_options(service, locations=location, parameters=parameter)

#     return options


# @util.jsonify
# def view_in_collection(name, service, location, parameter, use_cache=True, **kwargs):
#     """view dataset in collection 

#     """
#     collection = get_collection(name)
#     path = collection['path']
#     dataset = collection['datasets'][service]['data']
#     datafile_relpath = dataset[location][parameter]['relative_path']
#     datafile = os.path.join(path, datafile_relpath)
#     datatype = dataset[location][parameter]['datatype']
#     view = dataset[location][parameter].get('view')
    
#     if view is not None and use_cache:
#         return os.path.join(path, view)

#     view_file_base, ext = os.path.splitext(datafile_relpath)
#     view_file = None
#     if datatype=='timeseries':
#         view_file_relpath = view_file_base + '.png'
#         io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
#         df = io.read(datafile)
#         plt.style.use('ggplot')
#         title='%s: station %s' % (service, location)
#         if len(df.columns)>1:
#             df.plot(subplots=True, title=title, layout=(3, -1), figsize=(8, 10), color='r', sharex=True)
#         else:
#             df.plot(title=title, figsize=(8, 6))
#         view_file = os.path.join(path, view_file_relpath)
#         plt.savefig(view_file)
#         dataset[location][parameter]['view'] = view_file_relpath
#         _write_collection(collection)

#     if datatype=='raster':
#         if ext.lower()=='tif' or ext.lower()=='tiff':
#             view_file_relpath = datafile_relpath
#         else:
#             view_file_relpath = view_file_base + '.tif'
#             view_file = os.path.join(path, view_file_relpath)
#             import rasterio
#             with rasterio.drivers():
#                 rasterio.copy(datafile, view_file, driver='GTIFF')

#         dataset[location][parameter]['view'] = view_file_relpath
#         _write_collection(collection)        

#     return view_file



# @util.jsonify
# def get_collection(name, **kwargs):
#     """get a collection

#     Retreives collection metadata as a python dict

#     Parameters
#     ----------
#     name : str,
#         The name of the collection

#     Returns
#     -------
#     collection : dict,
#         A python dict representation of the collection, the collection is also 
#         written to a json file.
#     """
#     collection = _load_collections()[name]
#     with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE)) as f:
#         collection.update(json.load(f))

#     return collection


# @util.jsonify
# def delete_from_collection(name, service, location, parameter, **kwargs):
#     """delete (name, service, location, parameter) tuple from collection

#     DOES NOT DELETE ACTUAL DATA FILES JUST THE REFERENCES
#     """
#     collection = get_collection(name)
#     del collection['datasets'][service]['data'][location][parameter]
#     _write_collection(collection)

#     return collection





# def _write_collection(collection):
#     """write collection to json file

#     """
#     with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE), 'w') as f:
#         json.dump(collection, f)



