import json
import itertools

import pandas as pd
import numpy as np
import geojson
from shapely.geometry import shape

from .tasks import add_async
from .metadata import get_metadata
from .datasets import new_dataset
from .. import util
from ..plugins import load_providers
from ..static import DatasetSource, UriType
from ..database.database import get_db, db_session, select_datasets


@add_async
def add_datasets(collection, catalog_entries):
    """

    Args:
        collection (string, Required):
            name of collection
        catalog_entries (string, comma separated strings,list of strings, or pandas DataFrame, Required):
            list of ? to add to the collection.

    Returns:
        uris (list):
            uris of ?
    """
    if not isinstance(catalog_entries, pd.DataFrame):
        entries = get_metadata(catalog_entries, as_dataframe=True)

    uris = []
    for _, data in entries.iterrows():
        source = DatasetSource.WEB_SERVICE
        if 'quest' in data['service']:
            source = DatasetSource.DERIVED
        uri = new_dataset(collection=collection, catalog_entry=data.to_frame().transpose(), source=source)
        uris.append(uri)

    return uris


@add_async
def search_catalog(uris=None, expand=False, as_dataframe=False, as_geojson=False,
                   update_cache=False, filters=None, queries=None):
    """Retrieve list of catalog entries from resources.

    Args:
        uris (string or list, Required):
            uris of service_uris
        expand (bool, Optional, Default=False):
            if true then return metadata along with catalog entries
        as_dataframe (bool, Optional, Default=False):
           include catalog_entry details and format as a pandas DataFrame indexed by catalog_entry uris
        as_geojson (bool, Optional, Default=False):
            include catalog_entry details and format as a geojson scheme indexed by catalog_entry uris
        update_cache (bool, Optional,Default=False):
            if True, update metadata cache
        filters (dict, Optional, Default=None):
            filter catalog_entries by one or more of the available filters
                available filters:
                    bbox (string, optional): filter catalog_entries by bounding box
                    geom_type (string, optional): filter catalog_entries by geom_type,
                        i.e. point/line/polygon
                    parameter (string, optional): filter catalog_entries by parameter
                    display_name (string, optional):  filter catalog_entries by display_name
                    description (string, optional): filter catalog_entries by description
                    search_terms (list, optional): filter catalog_entries by search_terms

            catalog_entries can also be filtered by any other metadata fields
        queries(list, Optional, Default=None):
            list of string arguments to pass to pandas.DataFrame.query to filter the catalog_entries

    Returns:
        datasets (list, geo-json dict or pandas.DataFrame, Default=list):
             datasets of specified service(s), collection(s) or catalog_entry(s)

    """
    uris = list(itertools.chain(util.listify(uris) or []))

    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=[UriType.DATASET],
                                      raise_if_empty=False)

    services = grouped_uris.get(UriType.SERVICE) or []
    collections = grouped_uris.get(UriType.COLLECTION) or []

    catalog_entries = [d['catalog_entry'] for d in select_datasets(lambda c: c.collection.name in collections)]

    all_catalog_entries = list()

    filters = filters or dict()
    for name in services:
        provider, service, catalog_entry = util.parse_service_uri(name)
        if catalog_entry is not None:
            catalog_entries.append(name)
            continue
        provider_plugin = load_providers()[provider]
        tmp_catalog_entries = provider_plugin.search_catalog(service, update_cache=update_cache, **filters)
        all_catalog_entries.append(tmp_catalog_entries)

    if catalog_entries:
        all_catalog_entries.append(get_metadata(catalog_entries, as_dataframe=True))

    if all_catalog_entries:
        # drop duplicates fails when some columns have nested list/tuples like
        # _geom_coords. so drop based on index
        catalog_entries = pd.concat(all_catalog_entries)
        catalog_entries['index'] = catalog_entries.index
        catalog_entries = catalog_entries.drop_duplicates(subset='index')
        catalog_entries = catalog_entries.set_index('index').sort_index()
    else:
        catalog_entries = pd.DataFrame()

    # apply any specified filters
    for k, v in filters.items():
        if catalog_entries.empty:
            break  # if dataframe is empty then doesn't try filtering any further
        else:
            if k == 'bbox':
                bbox = util.bbox2poly(*[float(x) for x in util.listify(v)], as_shapely=True)
                idx = catalog_entries.intersects(bbox)  # http://geopandas.org/reference.html#GeoSeries.intersects
                catalog_entries = catalog_entries[idx]

            elif k == 'geom_type':
                idx = catalog_entries.geom_type.str.contains(v).fillna(value=False)
                catalog_entries = catalog_entries[idx]

            elif k == 'parameter':
                idx = catalog_entries.parameters.str.contains(v)
                catalog_entries = catalog_entries[idx]

            elif k == 'display_name':
                idx = catalog_entries.display_name.str.contains(v)
                catalog_entries = catalog_entries[idx]

            elif k == 'description':
                idx = catalog_entries.display_name.str.contains(v)
                catalog_entries = catalog_entries[idx]

            elif k == 'search_terms':
                idx = np.column_stack([
                    catalog_entries[col].apply(str).str.contains(search_term, na=False)
                    for col, search_term in itertools.product(catalog_entries.columns, v)
                ]).any(axis=1)
                catalog_entries = catalog_entries[idx]

            else:
                idx = catalog_entries.metadata.map(lambda x: _multi_index(x, k) == v)
                catalog_entries = catalog_entries[idx]

    if queries is not None:
        for query in queries:
            catalog_entries = catalog_entries.query(query)

    if not (expand or as_dataframe or as_geojson):
        return catalog_entries.index.astype('unicode').tolist()

    if as_geojson:
        if catalog_entries.empty:
            return geojson.FeatureCollection([])
        else:
            return json.loads(catalog_entries.to_json(default=util.to_json_default_handler))

    if not as_dataframe:
        catalog_entries = catalog_entries.to_dict(orient='index')

    return catalog_entries


def _multi_index(d, index):
    """Helper function for `search_catalog` filters to index multi-index tags (see `get_tags`)
    """
    if not isinstance(index, str):
        return d[index]

    multi_index = index.split(':')
    for k in multi_index:
        d = d[k]

    return d


def get_tags(service_uris, update_cache=False, filter=None, as_count=False):
    """Get searchable tags for a given service.

    Args:
        service_uris(string or list, Required):
            uris of providers
        update_cache(bool, Optional):
            if True, update metadata cache
        filter(list, Optional):
            list of tags to include in return value
        as_count(bool, Optional):
            if True, return dictionary with the number of values rather than a list of possible values

    Returns:
    --------
        tags (dict):
         dict keyed by tag name and list of possible values

         Note: nested dicts are parsed out as a multi-index tag where keys for nested dicts are joined with ':'.
    """
    # group uris by type
    grouped_uris = util.classify_uris(
        service_uris,
        as_dataframe=False,
        exclude=[UriType.COLLECTION, UriType.DATASET]
    )
    services = grouped_uris.get(UriType.SERVICE) or []

    tags = dict()

    for service in services:
        provider, service, _ = util.parse_service_uri(service)
        provider_plugin = load_providers()[provider]
        service_tags = provider_plugin.get_tags(service, update_cache=update_cache)
        tags.update(service_tags)

    if filter:
        tags = {k: v for k, v in tags.items() if k in filter}

    if as_count:
        return {k: len(v) for k, v in tags.items()}

    return tags


@add_async
def new_catalog_entry(geometry=None, geom_type=None, geom_coords=None, metadata=None):
    """Add a new entry to a catalog either a quest local catalog (table) or file.

    Args:
        geometry (string or Shapely.geometry.shape, optional, Default=None):
            well-known-text or Shapely shape representing the geometry of the catalog_entry.
            Alternatively `geom_type` and `geom_coords` can be passed.
        geom_type (string, Optional, Default=None):
             geometry type of catalog_entry (i.e. point/line/polygon)
        geom_coords (string or list, Optional, Default=None):
            geometric coordinates specified as valid geojson coordinates (i.e. a list of lists i.e.
            '[[-94.0, 23.2], [-94.2, 23.4] ...]'
            --------- OR ---------
            [[-94.0, 23.2], [-94.2, 23.4] ...] etc)
        metadata (dict, Optional, Default=None):
            optional metadata at the new catalog_entry

    Returns
    -------
        uri (string):
            uri of newly created entry

    """

    if geometry is None and geom_coords is not None and geom_type is not None:
        if isinstance(geom_coords, str):
            geom_coords = json.loads(geom_coords)

        geometry = shape({"coordinates": geom_coords, "type": geom_type})

    if hasattr(geometry, 'wkt'):
        geometry = geometry.wkt

    catalog_id = util.uuid('catalog_entry')

    data = {
        'service_id': catalog_id,
        'geometry': geometry,
        'metadata': metadata,
    }

    db = get_db()
    with db_session:
        db.QuestCatalog(**data)

    return util.construct_service_uri('quest', 'quest', catalog_id)
