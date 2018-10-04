import pandas as pd

from ..static import UriType
from ..plugins import load_providers
from ..util import classify_uris, construct_service_uri, parse_service_uri
from ..database import get_db, db_session, select_collections, select_datasets


def get_metadata(uris, as_dataframe=False):
    """Get metadata for uris.

    Args:
        uris (string, comma separated string, or list of strings, Required):
            list of uris to retrieve metadata for
        as_dataframe (bool, Optional, Default=False):
           include details of newly created dataset as a pandas Dataframe

    Returns:
        metadata (dict or pd.DataFrame, Default=dict):
            metadata at each uri keyed on uris
    """
    # group uris by type
    grouped_uris = classify_uris(uris)
    # handle case when no uris are passed in
    if not any(grouped_uris):
        metadata = pd.DataFrame()
        if not as_dataframe:
            metadata = metadata.to_dict(orient='index')
        return metadata

    metadata = []

    # get metadata for service type uris
    if UriType.SERVICE in grouped_uris.groups.keys():
        svc_df = grouped_uris.get_group(UriType.SERVICE)
        svc_df[['provider', 'service', 'catalog_id']] = svc_df['uri'].apply(parse_service_uri).apply(pd.Series)

        for (provider, service), grp in svc_df.groupby(['provider', 'service']):

            provider_plugin = load_providers()[provider]

            if not grp.query('catalog_id != catalog_id').empty:
                service_metadata = provider_plugin.get_services()[service]
                index = construct_service_uri(provider, service)
                metadata.append(pd.DataFrame(service_metadata, index=[index]))

            selected_catalog_entries = grp.query('catalog_id == catalog_id').uri.tolist()
            if selected_catalog_entries:
                catalog_entries = provider_plugin.search_catalog(service)
                catalog_entries = catalog_entries.loc[selected_catalog_entries]
                metadata.append(catalog_entries)

    if UriType.PUBLISHER in grouped_uris.groups.keys():
        svc_df = grouped_uris.get_group(UriType.PUBLISHER)
        svc_df[['provider', 'publish', 'catalog_id']] = svc_df['uri'].apply(parse_service_uri).apply(pd.Series)

        for (provider, publisher), grp in svc_df.groupby(['provider', 'publish']):
            provider_plugin = load_providers()[provider]
            publisher_metadata = provider_plugin.get_publishers()[publisher]
            index = construct_service_uri(provider, publisher)
            metadata.append(pd.DataFrame(publisher_metadata, index=[index]))

    if UriType.COLLECTION in grouped_uris.groups.keys():
        # get metadata for collections
        tmp_df = grouped_uris.get_group(UriType.COLLECTION)
        collections = select_collections(lambda c: c.name in tmp_df['uri'].tolist())
        collections = pd.DataFrame(collections)
        collections.set_index('name', inplace=True, drop=False)

        metadata.append(collections)

    if UriType.DATASET in grouped_uris.groups.keys():
        tmp_df = grouped_uris.get_group(UriType.DATASET)
        datasets = select_datasets(lambda c: c.name in tmp_df['uri'].tolist())
        datasets = pd.DataFrame(datasets)
        datasets.set_index('name', inplace=True, drop=False)
        metadata.append(datasets)

    metadata = pd.concat(metadata)

    if not as_dataframe:
        metadata = metadata.to_dict(orient='index')

    return metadata


def update_metadata(uris, display_name=None, description=None,
                    metadata=None, quest_metadata=None):
    """Update metadata for resource(s)

    Args:
        uris (string, comma separated string, or list of strings, Required):
            list of uris to update metadata for.
        display_name (string or list, Optional,Default=None):
            display name for each uri
        description (string or list, Optional,Default=None):
            description for each uri
        metadata (dict or list of dicts, Optional, Default=None):
            user defiend metadata
        quest_metadata (dict or list of dicts, Optional, Default=None):
            metadata used by QUEST
    Returns:
        metadata (dict):
            metadata at each uri keyed on uris
    """
    db = get_db()
    get_db_entity_funcs = {
        UriType.COLLECTION: lambda x: db.Collection[x],
        UriType.DATASET: lambda x: db.Dataset[x],
        UriType.SERVICE: lambda x: db.QuestCatalog[x.split('/')[-1]],
    }

    # group uris by type
    grouped_uris = classify_uris(uris, as_dataframe=True, exclude=[UriType.PUBLISHER], require_same_type=True)
    resource = list(grouped_uris.groups.keys())[0]
    uris = grouped_uris.get_group(resource)
    get_db_entity = get_db_entity_funcs[resource]

    if resource == UriType.SERVICE:
        # then make sure there are only quest catalog entries
        if not uris.uri.apply(lambda x: 'quest' in x).all():
            raise ValueError('Metadata on service catalog entries cannot be changed.')

    uris = uris.uri.tolist()
    n = len(uris)
    if n > 1:
        if display_name is None:
            display_name = [None] * n
        elif not isinstance(display_name, list):
            raise ValueError('display_name must be a list if more that one uri is passed in')

        if description is None:
            description = [None] * n
        elif not isinstance(description, list):
            raise ValueError('description must be a list if more that one uri is passed in')

        if not isinstance(metadata, list):
            metadata = [metadata] * n

        if not isinstance(quest_metadata, list):
                    quest_metadata = [quest_metadata] * n
    else:
        display_name = [display_name]
        description = [description]
        metadata = [metadata]
        quest_metadata = [quest_metadata]

    for uri, name, desc, meta, quest_meta in zip(uris, display_name, description, metadata, quest_metadata):
        if quest_meta is None:
            quest_meta = {}

        if name:
            quest_meta.update({'display_name': name})
        if desc:
            quest_meta.update({'description': desc})
        if meta:
            quest_meta.update({'metadata': meta})

        with db_session:
            entity = get_db_entity(uri)
            entity.set(**quest_meta)

    return get_metadata(uris)
