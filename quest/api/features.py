"""API functions related to Features.

Features are unique identifiers with a web service or collection.
"""
import json
import itertools
from jsonrpc import dispatcher
import pandas as pd
import geopandas as gpd
import geojson
import shapely.wkt
from shapely.geometry import shape, Polygon

from .. import util
from .database import get_db, db_session, select_features
from .collections import get_collections
from .metadata import get_metadata


@dispatcher.add_method
def add_features(collection, features):
    """Add features to a collection based on the passed in feature uris.

    This does not download datasets, it just adds features to a collection.
    When the features are added into a collection they are given a new
    feature id.

    If a feature from a service already exists, then it is not re-added instead the
    uri of the existing feature is returned (i.e. Feature was originally from
    usgs-nwis but is being copied from one collection to another) without
    over writing external_uri.

    Args:
        collection (string, Required):
            name of collection
        features (string, comma separated strings,list of strings, or pandas DataFrame, Required):
            list of features to add to the collection.

    Returns:
        uris (list):
            uris of features
    """

    if collection not in get_collections():
        raise ValueError('Collection {} does not exist'.format(collection))

    if not isinstance(features, pd.DataFrame):
        features = get_metadata(features, as_dataframe=True)

    db = get_db()
    with db_session:
        uris = []  # feature uris inside collection
        for _, data in features.iterrows():
            data = data.to_dict()
            row = db.Feature.select(lambda c:
                                    c.service == data['service'] and
                                    c.service_id == data['service_id'] and
                                    c.collection.name == collection
                                    ).first()
            if row is not None:
                uris.append(row.name)
                continue

            uri = util.uuid('feature')
            geometry = data['geometry']
            if hasattr(geometry, 'wkt'):
                geometry = geometry.wkt
            data.update({
                    'name': uri,
                    'collection': collection,
                    'geometry': geometry,
                    })
            db.Feature(**data)
            uris.append(uri)

    return uris


@dispatcher.add_method
def get_features(uris=None, expand=False, as_dataframe=False, as_geojson=False,
                 update_cache=False, filters=None,
                 services=None, collections=None, features=None):
    """Retrieve list of features from resources.

    Args:
        uris (string or list, Required):
            uris of services, collections, or features
        as_dataframe (bool, Optional, Default=False):
           include feature details and format as a pandas DataFrame indexed by feature uris
        as_geojson (bool, Optional, Default=False):
            include feature details and format as a geojson scheme indexed by feature uris
        update_cache (bool, Optional,Default=False):
            if True, update metadata cache
        filters (dict, Optional, Default=None):
            filter features by one or more of the available filters
                available filters:
                    geom_type (string, optional): filter features by geom_type,
                        i.e. point/line/polygon
                    parameter (string, optional): filter features by parameter
                    bbox (string, optional): filter features by bounding box

            Features can also be filtered by any other metadata fields
        services (comma separated strings, or list of strings, Deprecated):
            list of services to search in for features
        collections (comma separated strings or list of strings, Deprecated):
            list of collections to search in for features
        features (comma separated strings or list of strings, Deprecated):
            list of features to include in search

    Returns:
        features (list, geo-json dict or pandas.DataFrame, Default=list):
             features of specified service(s), collection(s) or feature(s)

    """
    uris = list(itertools.chain(util.listify(uris) or [],
                                util.listify(services) or [],
                                util.listify(collections) or [],
                                util.listify(features) or []))

    # group uris by type
    grouped_uris = util.classify_uris(uris, as_dataframe=False, exclude=['datasets'])

    if not any(grouped_uris):
        raise ValueError('At least one service, collection, or feature uri must be specified.')

    services = grouped_uris.get('services') or []
    collections = grouped_uris.get('collections') or []
    features = grouped_uris.get('features') or []

    all_features = []

    # get metadata for directly specified features
    if features is not None:
        all_features.append(get_metadata(features, as_dataframe=True))

    # get metadata for features in services
    for name in services:
        provider, service, feature = util.parse_service_uri(name)
        tmp_feats = _get_features(provider, service, update_cache=update_cache)
        all_features.append(tmp_feats)

    # get metadata for features in collections
    tmp_feats = select_features(lambda c: c.collection.name in collections)
    tmp_feats = gpd.GeoDataFrame(tmp_feats)

    if not tmp_feats.empty:
        tmp_feats['geometry'] = tmp_feats['geometry'].apply(
                                    lambda x: x if x is None else shapely.wkt.loads(x))
        tmp_feats.set_geometry('geometry')

        tmp_feats.index = tmp_feats['name']
    all_features.append(tmp_feats)

    # drop duplicates fails when some columns have nested list/tuples like
    # _geom_coords. so drop based on index
    features = pd.concat(all_features)
    features['index'] = features.index
    features = features.drop_duplicates(subset='index')
    features = features.set_index('index').sort_index()

    # apply any specified filters
    if filters is not None:
        for k, v in filters.items():
            if features.empty:
                break  # if dataframe is empty then doen't try filtering any further
            else:
                if k == 'bbox':
                    bbox = util.bbox2poly(*[float(x) for x in util.listify(v)], as_shapely=True)
                    idx = features.intersects(bbox)  # http://geopandas.org/reference.html#GeoSeries.intersects
                    features = features[idx]

                elif k == 'geom_type':
                    idx = features.geom_type.str.contains(v)  # will not work if features is empty
                    features = features[idx]

                elif k == 'parameter':
                    idx = features.parameters.str.contains(v)
                    features = features[idx]

                elif k == 'display_name':
                    idx = features.display_name.str.contains(v)
                    features = features[idx]

                elif k == 'description':
                    idx = features.display_name.str.contains(v)
                    features = features[idx]

                else:
                    idx = features.metadata.map(lambda x: x.get(k) == v)
                    features = features[idx]

    if not (expand or as_dataframe or as_geojson):
        return features.index.astype('unicode').tolist()

    if as_geojson:
        if features.empty:
            return geojson.FeatureCollection([])
        else:
            return json.loads(features.to_json(default=util.to_json_default_handler))

    if not as_dataframe:
        features = features.to_dict(orient='index')

    return features


@dispatcher.add_method
def get_tags(service):
    """Get searchable tags for a given service.

    Args:
        service(string):
         name of service

    Returns:
    --------
        tags (dict):
         dict keyed by tag name and list of possible values
    """
    f = get_features(services=service, as_dataframe=True)

    # potential tags are non underscored column names
    tags = {}
    for tag in [x for x in f.columns if not x.startswith('_')]:
        try:
            df = f[tag].dropna()
            tag_list = df.unique().tolist()
            if len(tag_list) < len(df):
                tags[tag] = tag_list
        except TypeError:
            # for fields that have unhashable types like list
            # unique doesn't work
            continue

    return tags


@dispatcher.add_method
def new_feature(collection, display_name=None, geometry=None, geom_type=None, geom_coords=None,
                description=None, metadata=None):
    """Add a new feature to a collection.

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
            uri of newly created feature

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


def _get_features(provider, service, update_cache):
    driver = util.load_services()[provider]
    features = driver.get_features(service, update_cache=update_cache)
    features['service'] = 'svc://{}:{}'.format(provider, service)
    features['service_id'] = features.index
    features.index = features['service'] + '/' + features['service_id']
    features['name'] = features.index
    return features
