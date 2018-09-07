import json
import itertools
import pandas as pd
import numpy as np
import geopandas as gpd
import geojson
import shapely.wkt
from shapely.geometry import shape

from .. import util
from .. import plugins
from quest.database.database import get_db, db_session, select_datasets
from .collections import get_collections
from .metadata import get_metadata
from .tasks import add_async


@add_async
def add_datasets(collection, datasets):
    """

    Args:
        collection (string, Required):
            name of collection
        datasets (string, comma separated strings,list of strings, or pandas DataFrame, Required):
            list of ? to add to the collection.

    Returns:
        uris (list):
            uris of ?
    """

    if collection not in get_collections():
        raise ValueError('Collection {} does not exist'.format(collection))

    if not isinstance(datasets, pd.DataFrame):
        datasets = get_metadata(datasets, as_dataframe=True)

    db = get_db()
    with db_session:
        uris = []  # dataset uris inside collection
        for _, data in datasets.iterrows():
            data = data.to_dict()
            row = db.Dataset.select(lambda c:
                                    c.entry_service == data['service'] and
                                    c.catalog_entry == data['service_id'] and
                                    c.collection.name == collection
                                    ).first()
            if row is not None:
                uris.append(row.name)
                continue

            uri = util.uuid('dataset')
            geometry = data['geometry']
            if hasattr(geometry, 'wkt'):
                geometry = geometry.wkt
            data.update({
                    'name': uri,
                    'collection': collection,
                    'geometry': geometry,
                    })

            # ensure dates are serialized before loading into database
            data = json.loads(json.dumps(data, default=util.to_json_default_handler))
            db.Dataset(**data)
            uris.append(uri)

    return uris


@add_async
def search_catalog(uris=None, expand=False, as_dataframe=False, as_geojson=False,
                 update_cache=False, filters=None, queries=None,
                 services=None, collections=None, datasets=None):
    """Retrieve list of catalog entries from resources.

    Args:
        uris (string or list, Required):
            uris of providers, collections, or ?
        as_dataframe (bool, Optional, Default=False):
           include feature details and format as a pandas DataFrame indexed by feature uris
        as_geojson (bool, Optional, Default=False):
            include feature details and format as a geojson scheme indexed by feature uris
        update_cache (bool, Optional,Default=False):
            if True, update metadata cache
        filters (dict, Optional, Default=None):
            filter ? by one or more of the available filters
                available filters:
                    geom_type (string, optional): filter ? by geom_type,
                        i.e. point/line/polygon
                    parameter (string, optional): filter ? by parameter
                    bbox (string, optional): filter ? by bounding box

            ? can also be filtered by any other metadata fields
        queries(list, Optional, Default=None):
            list of string arguments to pass to pandas.DataFrame.query to filter the ?
        services (comma separated strings, or list of strings, Deprecated):
            list of providers to search in for ?
        collections (comma separated strings or list of strings, Deprecated):
            list of collections to search in for ?
        datasets (comma separated strings or list of strings, Deprecated):
            list of ? to include in search

    Returns:
        datasets (list, geo-json dict or pandas.DataFrame, Default=list):
             datasets of specified service(s), collection(s) or feature(s)

    """
    uris = list(itertools.chain(util.listify(uris) or [],
                                util.listify(services) or [],
                                util.listify(collections) or [],
                                util.listify(datasets) or []))

    # group uris by type
    # This might cause some problems.
    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=['datasets'])

    if not any(grouped_uris):
        raise ValueError('At least one service, collection, or feature uri must be specified.')

    services = grouped_uris.get('services') or []
    collections = grouped_uris.get('collections') or []
    features = grouped_uris.get('datasets') or []

    all_datasets = []

    # get metadata for directly specified ?
    if features is not None:
        all_datasets.append(get_metadata(datasets, as_dataframe=True))

    # get metadata for ? in providers
    filters = filters or dict()
    for name in services:
        provider, service, feature = util.parse_service_uri(name)
        provider_plugin = plugins.load_providers()[provider]
        tmp_datasets = provider_plugin.search_catalog(service, update_cache=update_cache, **filters)
        all_datasets.append(tmp_datasets)

    # get metadata for datasets in collections
        tmp_datasets = select_datasets(lambda c: c.collection.name in collections)
        tmp_datasets = gpd.GeoDataFrame(tmp_datasets)

    if not tmp_datasets.empty:
        tmp_datasets['geometry'] = tmp_datasets['geometry'].apply(
                                    lambda x: x if x is None else shapely.wkt.loads(x))
        tmp_datasets.set_geometry('geometry')

        tmp_datasets.index = tmp_datasets['name']
    all_datasets.append(tmp_datasets)

    # drop duplicates fails when some columns have nested list/tuples like
    # _geom_coords. so drop based on index
    datasets = pd.concat(all_datasets)
    datasets['index'] = datasets.index
    datasets = datasets.drop_duplicates(subset='index')
    datasets = datasets.set_index('index').sort_index()

    # apply any specified filters
    # features = features.dropna(axis=1)  # can't index if NaN values exist
    for k, v in filters.items():
        if features.empty:
            break  # if dataframe is empty then doesn't try filtering any further
        else:
            if k == 'bbox':
                bbox = util.bbox2poly(*[float(x) for x in util.listify(v)], as_shapely=True)
                idx = features.intersects(bbox)  # http://geopandas.org/reference.html#GeoSeries.intersects
                datasets = datasets[idx]

            elif k == 'geom_type':
                idx = features.geom_type.str.contains(v).fillna(value=False)  # will not work if features is empty
                datasets = datasets[idx]

            elif k == 'parameter':
                idx = features.parameters.str.contains(v)
                datasets = datasets[idx]

            elif k == 'display_name':
                idx = features.display_name.str.contains(v)
                datasets = datasets[idx]

            elif k == 'description':
                idx = datasets.display_name.str.contains(v)
                features = datasets[idx]

            elif k == 'search_terms':
                idx = np.column_stack([datasets[col].apply(str).str.contains(search_term, na=False)
                                       for col, search_term in itertools.product(datasets.columns, v)]).any(axis=1)
                datasets = datasets[idx]

            else:
                idx = datasets.metadata.map(lambda x: _multi_index(x, k) == v)
                datasets = datasets[idx]

    if queries is not None:
        for query in queries:
            datasets = datasets.query(query)

    if not (expand or as_dataframe or as_geojson):
        return datasets.index.astype('unicode').tolist()

    if as_geojson:
        if datasets.empty:
            return geojson.FeatureCollection([])
        else:
            return json.loads(datasets.to_json(default=util.to_json_default_handler))

    if not as_dataframe:
        datasets = datasets.to_dict(orient='index')

    return datasets


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
    grouped_uris = util.classify_uris(service_uris, as_dataframe=False, exclude=['collections', 'features', 'datasets'])
    services = grouped_uris.get('services') or []

    tags = dict()

    for service in services:
        provider, service, feature = util.parse_service_uri(service)
        provider_plugin = plugins.load_providers()[provider]
        service_tags = provider_plugin.get_tags(service, update_cache=update_cache)
        tags.update(service_tags)

    if filter:
        tags = {k: v for k, v in tags.items() if k in filter}

    if as_count:
        return {k: len(v) for k, v in tags.items()}

    return tags


@add_async
def new_catalog_entry(collection, display_name=None, geometry=None, geom_type=None, geom_coords=None,
                description=None, metadata=None):
    """Add a new entry to a collection.

    Args:
        collection (string, Required):
            name of collection
        display_name (string, Optional, Default=None):
            display name of feature
        geometry (string or Shapely.geometry.shape, optional, Default=None):
            well-known-text or Shapely shape representing the geometry of the feature. Alternatively `geom_type` and `geom_coords` can be passed.
        geom_type (string, Optional, Default=None):
             geometry type of feature (i.e. point/line/polygon)
        geom_coords (string or list, Optional, Default=None):
            geometric coordinates specified as valid geojson coordinates (i.e. a list of lists i.e.
            '[[-94.0, 23.2], [-94.2, 23.4] ...]'
            --------- OR ---------
            [[-94.0, 23.2], [-94.2, 23.4] ...] etc)
        description (string, Optional, Default=None):
            description of feature
        metadata (dict, Optional, Default=None):
            optional metadata at the new feature

    Returns
    -------
        uri (string):
            uri of newly created entry

    """
    if collection not in get_collections():
        raise ValueError('Collection {} not found'.format(collection))

    if geometry is None and geom_coords is not None and geom_type is not None:
        if isinstance(geom_coords, str):
            geom_coords = json.loads(geom_coords)

        geometry = shape({"coordinates": geom_coords, "type": geom_type})

    if hasattr(geometry, 'wkt'):
        geometry = geometry.wkt

    uri = util.uuid('feature')
    if display_name is None:
        display_name = uri

    if description is None:
        description = uri

    data = {
            'name': uri,
            'display_name': display_name,
            'description': description,
            'collection': collection,
            'geometry': geometry,
            'metadata': metadata,
            }

    db = get_db()
    with db_session:
        db.Feature(**data)

    return uri
