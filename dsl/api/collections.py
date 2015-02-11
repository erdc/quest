"""API functions related to Collections

"""
from .. import util
from .services import get_locations, get_data, get_parameters
import datetime
import json
import os

COLLECTIONS_FILE = 'collections.json'
COLLECTION_METADATA_FILE = 'collection.json'
METADATA_FILE = 'dsl.json'


def add_to_collection(name, service, locations, parameters=None):
	"""

		locations are location ids
		parameters None or comma separated
	"""
	collection = get_collection(name)
	
	if 'datasets' not in collection.keys():
		collection['datasets'] = {}

	if service not in collection['datasets'].keys():
		collection['datasets'][service] = {'data': {}, 'locations':{} }

	dataset = collection['datasets'][service]

	features = get_locations(service, locations)
	dataset['locations'] = _append_features(dataset['locations'], features)
	
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
	"""For now just downloaded all in collection

	"""
	collection = get_collection(name)
	for service, dataset in collection['datasets'].iteritems():
		for location, parameters in dataset['data'].iteritems():
			path = collection['path']
			data_locations = get_data(service, location, path=path, parameters=','.join(parameters.keys()))
			for k, v in data_locations.iteritems():
				print '%s:%s' % (k,v)
				parameters[k]['relative_path'] = os.path.relpath(v, path)
	_write_collection(collection)
	return collection


def new_collection(name, path=None, tags=None):
	collections = _load_collections()

	if name in collections.keys():
		print 'Collection Already Exists'
		return get_collection(name)

	if not path:
		path = util.get_dsl_dir()

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
	collections = _load_collections()

	if not name in collections.keys():
		print 'Collection not found'
		return

	del collections[name]
	_write_collections(collections)
	return collections


def list_collections():
	return _load_collections()


def get_collection(name):
	collection = _load_collections()[name]
	with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE)) as f:
		collection.update(json.load(f))

	collection['name'] = name
	return collection


def update_collection(name):
    raise NotImplementedError('Updating Collections has not been implemented')


def delete_from_collection(name, service, feature_ids):
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


def _append_features(old, new):
	if not old:
		return new

	existing_features = [feature['id'] for feature in old['features']]
	for feature in new['features']:
		if feature['id'] not in existing_features:
			old['features'].append(feature)

	return old


def _load_collections():
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)

	if not os.path.exists(path):
		return {}

	with open(path) as f:
		return json.load(f)


def _write_collection(collection):
	with open(os.path.join(collection['path'], COLLECTION_METADATA_FILE), 'w') as f:
		json.dump(collection, f)


def _write_collections(collections):
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)
	with open(path, 'w') as f:
		json.dump(collections, f)
