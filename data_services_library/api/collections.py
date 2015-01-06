"""
api functions related to handling collections
"""
from .. import util
import json
import os

COLLECTIONS_FILE = 'collections.json'
METADATA_FILE = 'dsl.json'


def add_to_collection(name, data):
	pass


def create_collection(name, path=None, tags=None):
	collections = _load_collections()

	if get(name=name):
		print 'Collection Already Exists'
		return 

	if not path:
		path = util.get_dsl_dir()

	collection_path = os.path.join(path, name)
	util.mkdir_if_doesnt_exist(collection_path)

	collection = {'name': name, 'path': collection_path}
	collections.append(collection)
	_write_collections(collections)

	return collection


def delete_collection(name):
	collections = _load_collections()

	if not get(name=name):
		print 'Collection not found'
		return

	collections = [collection for collection in collections if collection['name']!=name]

	_write_collections(collections)
	return collections


def list_collections():
	return _load_collections()


def retrieve_collection(name):
	return [collection for collection in _load_collections() if collection['name']==name]	


def update_collection(name):
    pass


def delete_from_collection(name, feature_id):
    pass


def _load_collections():
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)

	if not os.path.exists(path):
		return []

	with open(path) as f:
		return json.load(f)


def _write_collections(collections):
	path = os.path.join(util.get_dsl_dir(), COLLECTIONS_FILE)
	with open(path, 'w') as f:
		json.dump(collections, f)
