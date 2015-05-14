"""API functions related to Collections

"""
from .. import util
from .services import get_services, get_locations, get_data, get_data_options, get_parameters
import datetime
import json
import matplotlib.pyplot as plt
from matplotlib import style
import os
from ..settings import COLLECTION_METADATA_FILE
import warnings


@util.jsonify
def add_to_collection(name, service, locations, parameters=None, **kwargs):
    """adds locations from a service to a collection

    Note: Data is not downloaded in this function call. Placeholders
    are placed in the collection. To download data call function
    download_in_collection

    Parameters
    ----------
    name : str,
        The name of the collection 
    service : str,
        The name of the service
    locations : str,
        comma separated list of locations. These are location codes or ids 
        of the locations to be added from a service
    parameters : ``None`` or str,
        comma separated list of parameters to download for each location. If 
        ``None`` (default) is passed then all available parameters for that 
        service will be used.

    Returns
    -------
    collection : dict, 
        A python dict representation of the collection, the collection is also 
        written to a json file.
    """

    if isinstance(locations, dict):
        features = locations
        locations = [loc['id'] for loc in features['features']]
    else:
        locations = util.listify(locations)
        features = get_locations(service, locations)

    parameters = util.listify(parameters)
    if parameters is None:
        parameters = get_parameters(service)

    collection = get_collection(name)
    
    if 'datasets' not in collection.keys():
        collection['datasets'] = {}

    if service not in collection['datasets'].keys():
        collection['datasets'][service] = {'data': {}, 'locations':{} }

    dataset = collection['datasets'][service]


    dataset['locations'] = util.append_features(dataset['locations'], features)

    for loc, feature in zip(locations, features['features']):
        if loc not in dataset['data'].keys():
            relative_path = feature['properties'].get('relative_path')
            dataset['data'][loc] = {p:{'relative_path': relative_path} for p in parameters} 
        else:
            params = dataset['data'][loc]['parameters']
            dataset['data'][loc]['parameters'] = list(set(params + parameters))
    
    _write_collection(collection)
    return collection


@util.jsonify
def download_in_collection(name, service=None, location=None, parameter=None, **kwargs):
    """download data for services/locations/parameters present in collection

    Currently *all* datasets present in a collection will be downloaded with 
    default download options. The data is downloaded to subfolders in the 
    collection folder and a relative path reference is placed in the collection
    metadata. A separate file is saved for each service/location/parameter tuple.

    Parameters
    ----------
    name : str,
        The name of the collection

    Returns
    -------
    collection : dict, 
        A python dict representation of the collection, the collection is also 
        written to a json file.

    """
    collection = get_collection(name)

    if not any([service, location, parameter]):
        for service, dataset in collection['datasets'].iteritems():
            datatype = get_services(names=service)[0].get('datatype')
            for location, parameters in dataset['data'].iteritems():
                path = collection['path']
                data_files = get_data(service, location, path=path, parameters=','.join(parameters.keys()))
                for parameter, v in data_files[location].iteritems():
                    if v is None:
                        msg = "Warning: No data available for (service: %s, location: %s, parameter: %s)" % (service, location, parameter)
                        warnings.warn(msg)
                    else:
                        parameters[parameter]['relative_path'] = os.path.relpath(v, path)
                        dataset['data'][location][parameter]['datatype'] = datatype
    else:
        dataset = collection['datasets'][service]['data']
        path = collection['path']
        data_file = get_data(service, location, path=path, parameters=parameter, **kwargs)
        datatype = get_services(names=service)[0].get('datatype')
        data_path = data_file[location].get(parameter)
        if data_path is None:
            msg = "Warning: No data available for (service: %s, location: %s, parameter: %s)" % (service, location, parameter)
            warnings.warn(msg)
        else:
            dataset[location][parameter]['relative_path'] = os.path.relpath(data_path, path)
            dataset[location][parameter]['datatype'] = datatype

    _write_collection(collection)
    return collection


@util.jsonify
def download_in_collection_options(name, service=None, location=None, parameter=None):
    collection = get_collection(name)

    options = {}
    if not any([service, location, parameter]):
        for service, dataset in collection['datasets'].iteritems():
            options[service] = {}
            for location, parameters in dataset['data'].iteritems():
                options[service][location] = {}
                for parameter in parameters:
                    print service, location, parameter
                    options[service][location][parameter] = get_data_options(service, locations=location, parameters=parameter)
    else:
        options[service] = {}
        options[service][location] = {}
        options[service][location][parameter] = get_data_options(service, locations=location, parameters=parameter)

    return options


@util.jsonify
def view_in_collection(name, service, location, parameter, **kwargs):
    """view dataset in collection 

    """
    collection = get_collection(name)
    path = collection['path']
    dataset = collection['datasets'][service]['data']
    datafile_relpath = dataset[location][parameter]['relative_path']
    datafile = os.path.join(path, datafile_relpath)
    datatype = dataset[location][parameter]['datatype']
    view = dataset[location][parameter].get('view')
    
    if view is not None:
        return os.path.join(path, view)

    view_file_base, ext = os.path.splitext(datafile_relpath)
    view_file = None
    if datatype=='timeseries':
        view_file_relpath = view_file_base + '.png'
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
        df = io.read(datafile)
        style.use('fivethirtyeight')
        df.plot()
        view_file = os.path.join(path, view_file_relpath)
        plt.savefig(view_file)
        dataset[location][parameter]['view'] = view_file_relpath
        _write_collection(collection)

    if datatype=='raster':
        if ext.lower()=='tif' or ext.lower()=='tiff':
            view_file_relpath = datafile_relpath
        else:
            view_file_relpath = view_file_base + '.tif'
            view_file = os.path.join(path, view_file_relpath)
            import rasterio
            with rasterio.drivers():
                rasterio.copy(datafile, view_file, driver='GTIFF')

        dataset[location][parameter]['view'] = view_file_relpath
        _write_collection(collection)        

    return view_file


@util.jsonify
def new_collection(name, path=None, tags=None, **kwargs):
    """create a new collection

    Create a new collection by creating a new folder and placing a json
    file in the folder for dsl metadata and adding a reference to the 
    master collections metadata folder.

    Parameters
    ----------
    name : str,
        The name of the collection
    path: ``None`` or str,
        If ``None`` use default dsl location for collections otherwise use specified path. 

    Returns
    -------
    collection : dict,
        A python dict representation of the collection, the collection is also 
        written to a json file.
    """

    collections = _load_collections()

    if name in collections.keys():
        print 'Collection Already Exists'
        return get_collection(name)

    if not path:
        path = os.path.join(util.get_dsl_dir(), 'collections')

    collection_path = os.path.join(path, name)
    util.mkdir_if_doesnt_exist(collection_path)

    collection = {'name': name, 'path': collection_path}
    metadata = {'created_on' : datetime.datetime.now().isoformat(), 'datasets': {}}

    with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE), 'w') as f:
        json.dump(metadata, f)

    collections[name] = collection
    _write_collections(collections)

    return collection


@util.jsonify
def delete_collection(name, **kwargs):
    """delete a collection

    Deletes a collection from the collections metadata file.

    Note: This currently does not delete folders and/or data present 
    in the collection folder, it just removes the reference from the
    master metadata file.

    Parameters
    ----------
    name : str,
        The name of the collection

    Returns
    -------
    collections : dict,
        A python dict representation of the list of available collections, 
        the updated collections list is also written to a json file.
    """
    collections = _load_collections()

    if not name in collections.keys():
        print 'Collection not found'
        return

    del collections[name]
    _write_collections(collections)
    return collections


@util.jsonify
def list_collections(**kwargs):
    """list all available collections

    Returns
    -------
    collections : dict,
        A python dict representation of the list of available collections, 
        the updated collections list is also written to a json file.
    """
    return _load_collections()


@util.jsonify
def get_collection(name, **kwargs):
    """get a collection

    Retreives collection metadata as a python dict

    Parameters
    ----------
    name : str,
        The name of the collection

    Returns
    -------
    collection : dict,
        A python dict representation of the collection, the collection is also 
        written to a json file.
    """
    collection = _load_collections()[name]
    with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE)) as f:
        collection.update(json.load(f))

    return collection


@util.jsonify
def update_collection(name, **kwargs):
    """Not sure of function, maybe allow moving to different path etc

    NOT IMPLEMENTED
    """
    raise NotImplementedError('Updating Collections has not been implemented')


@util.jsonify
def delete_from_collection(name, service, feature_ids, **kwargs):
    """delete locations? from collection

    NOT IMPLEMENTED 
    """
    raise NotImplementedError('Deleting from collections has not been implemented')

    if not isinstance(feature_ids, list):
        feature_ids = [feature_ids]

    collection = get_collection(name)
    service = collection['service'].get(service)
    if service:
        dataset['features']['features'] = [feature for feature in dataset['features']['features'] if feature['id'] not in feature_ids]
    
        if not dataset['features']['features']:
            del collection['datasets'][service]

        _write_collection(collection)

    return collection


def _load_collections():
    """load list of collections

    """
    path = util.get_collections_index()

    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return json.load(f)


def _write_collection(collection):
    """write collection to json file

    """
    with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE), 'w') as f:
        json.dump(collection, f)


def _write_collections(collections):
    """write list of collections to json file 
    """
    path = util.get_collections_index()
    with open(path, 'w') as f:
        json.dump(collections, f)
