"""API functions related to Collections

"""
from .. import util
from .services import get_locations, get_data, get_parameters
import datetime
import json
import os

COLLECTIONS_FILE = 'collections/collections.json' #master file
COLLECTION_METADATA_FILE = 'dsl_metadata.json' #individual collection metadata
METADATA_FILE = 'dsl.json'


def add_to_collection(name, service, locations, parameters=None):
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
	collection = get_collection(name)
	
	if 'datasets' not in collection.keys():
		collection['datasets'] = {}

	if service not in collection['datasets'].keys():
		collection['datasets'][service] = {'data': {}, 'locations':{} }

	dataset = collection['datasets'][service]

	features = get_locations(service, locations)
	dataset['locations'] = util.append_features(dataset['locations'], features)
	
	if parameters:
		parameters = parameters.split(',')
	else:
		parameters = get_parameters(service)

	for loc in locations.split(','):
		if loc not in dataset['data'].keys():
			dataset['data'][loc] = {p:{'relative_path': None} for p in parameters} 
		else:
			params = dataset['data'][loc]['parameters']
			dataset['data'][loc]['parameters'] = list(set(params + parameters))
	
	_write_collection(collection)
	return collection


def download_in_collection(name):
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
	for service, dataset in collection['datasets'].iteritems():
		for location, parameters in dataset['data'].iteritems():
			path = collection['path']
			data_files = get_data(service, location, path=path, parameters=','.join(parameters.keys()))
			for k, v in data_files[location].iteritems():
				parameters[k]['relative_path'] = os.path.relpath(v, path)
	_write_collection(collection)
	return collection


def new_collection(name, path=None, tags=None):
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

	collection = {'path': collection_path}
	metadata = {'created_on' : datetime.datetime.now().isoformat(), 'datasets': {}}

	with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE), 'w') as f:
		json.dump(metadata, f)

	collections[name] = collection
	_write_collections(collections)

	return collections


def delete_collection(name):
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


def list_collections():
	"""list all available collections

	Returns
	-------
    collections : dict,
    	A python dict representation of the list of available collections, 
    	the updated collections list is also written to a json file.
	"""
	return _load_collections()


def get_collection(name):
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

	collection['name'] = name
	return collection


def update_collection(name):
	"""Not sure of function, maybe allow moving to different path etc

	NOT IMPLEMENTED
	"""
    raise NotImplementedError('Updating Collections has not been implemented')


def delete_from_collection(name, service, feature_ids):
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
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)

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
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)
	with open(path, 'w') as f:
		json.dump(collections, f)
