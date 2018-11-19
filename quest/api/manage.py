import os
import shutil

from .tasks import add_async
from .projects import _get_project_dir
from .collections import get_collections
from .metadata import get_metadata, update_metadata
from ..static import UriType, DatasetSource
from ..util import logger, classify_uris, uuid, parse_service_uri
from ..database.database import get_db, db_session, select_datasets


@add_async
def delete(uris):
    """Delete metadata for resource(s)

    WARNING:
        deleting a collection deletes all associated datasets

    Args:
        uris (string, comma separated string or list of strings, Required):
            uri(s) of collection, and/or dataset to delete

    Returns:
        status (bool):
            True on success

    """
    # if uri list is empty do nothing
    if not uris:
        return True

    # group uris by type
    grouped_uris = classify_uris(uris,
                                 as_dataframe=False,
                                 exclude=[UriType.SERVICE, UriType.PUBLISHER],
                                 require_same_type=True)
    resource = list(grouped_uris)[0]
    uris = grouped_uris[resource]

    db = get_db()
    for uri in uris:
        if resource == UriType.COLLECTION:
            if uri not in get_collections():
                logger.error('Collection does not exist: %s', uri)
                raise ValueError('Collection does not exists')

            with db_session:
                datasets = db.Dataset.select(lambda d: d.collection.name == uri)
                if datasets.count() > 0:
                    datasets.delete()
                db.Collection[uri].delete()

            path = _get_project_dir()
            path = os.path.join(path, uri)
            if os.path.exists(path):
                logger.info('deleting all data under path: %s' % path)
                shutil.rmtree(path)

        if resource == UriType.DATASET:
            with db_session:
                dataset = db.Dataset[uri]

                if dataset.source == DatasetSource.DERIVED:
                    catalog_entry_datasets = select_datasets(lambda d: d.catalog_entry == dataset.catalog_entry)

                    if len(catalog_entry_datasets) == 1:
                        _, _, catalog_id = parse_service_uri(dataset.catalog_entry)
                        db.QuestCatalog[catalog_id].delete()

                try:
                    os.remove(dataset.file_path)
                except (OSError, TypeError):
                    pass

                dataset.delete()

    return True


@add_async
def move(uris, destination_collection, as_dataframe=None, expand=None):

    if not uris:                                                                                                                        
        return {}                                                                                                                       

    grouped_uris = classify_uris(uris,
                                 as_dataframe=False,
                                 exclude=[UriType.SERVICE, UriType.PUBLISHER, UriType.COLLECTION],
                                 require_same_type=True)
    resource = list(grouped_uris)[0]                                                                                                    
    uris = grouped_uris[resource]                                                                                                       
    project_path = _get_project_dir()                                                                                                   
    destination_collection_path = os.path.join(project_path, destination_collection)                                                    

    new_datasets = []

    for uri in uris:
        if resource == UriType.DATASET:
            dataset_metadata = get_metadata(uri)[uri]                                                                                   
            collection_path = os.path.join(project_path, dataset_metadata['collection'])
            _move_dataset(dataset_metadata, collection_path, destination_collection_path)
            new_datasets.append(uri)

    if expand or as_dataframe:
        new_datasets = get_metadata(new_datasets, as_dataframe=as_dataframe)

        if as_dataframe:
            new_datasets['quest_type'] = 'dataset'
            return new_datasets

    return new_datasets


@add_async
def copy(uris, destination_collection, as_dataframe=None, expand=None):

    if not uris:                                                                                                                        
        return {}                                                                                                                       

    grouped_uris = classify_uris(uris,
                                 as_dataframe=False,
                                 exclude=[UriType.SERVICE, UriType.PUBLISHER, UriType.COLLECTION],
                                 require_same_type=True)
    resource = list(grouped_uris)[0]                                                                                                    
    uris = grouped_uris[resource]                                                                                                       
    project_path = _get_project_dir()                                                                                                   
    destination_collection_path = os.path.join(project_path, destination_collection)                                                    

    new_datasets = []

    for uri in uris:
        if resource == UriType.DATASET:
            dataset_metadata = get_metadata(uri)[uri]                                                                                   
            collection_path = os.path.join(project_path, dataset_metadata['collection'])

            new_datasets.append(_copy_dataset(dataset_metadata, collection_path, destination_collection_path))

    if expand or as_dataframe:
        new_datasets = get_metadata(new_datasets, as_dataframe=as_dataframe)

        if as_dataframe:
            new_datasets['quest_type'] = 'dataset'
            return new_datasets

    return new_datasets


def _copy_dataset(dataset_metadata, collection_path, destination_collection_path):
    new_name = uuid('dataset')
    db = get_db()
    with db_session:
        db_metadata = db.Dataset[dataset_metadata['name']].to_dict()
        db_metadata.update(name=new_name)
        db.Dataset(**db_metadata)
    
    _update_dataset_file_location(shutil.copy2, db_metadata, collection_path, destination_collection_path)
    return new_name


def _move_dataset(dataset_metadata, collection_path, destination_collection_path):
    _update_dataset_file_location(shutil.move, dataset_metadata, collection_path, destination_collection_path)


def _update_dataset_file_location(func, dataset_metadata, collection_path, destination_collection_path):
    quest_metadata = {}
    file_path = dataset_metadata['file_path']
    if file_path is not None:
        rel_path = os.path.relpath(file_path, collection_path)
        new_file_path = os.path.normpath(os.path.join(destination_collection_path, rel_path))
        quest_metadata['file_path'] = new_file_path

        os.makedirs(os.path.split(new_file_path)[0], exist_ok=True)
        func(file_path, new_file_path)

    update_metadata(dataset_metadata['name'], quest_metadata=quest_metadata)
