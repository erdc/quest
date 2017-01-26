"""API functions related to Features.

Features are unique identifiers with a web service or collection.
"""
import json
from jsonrpc import dispatcher
import pandas as pd
import geopandas as gpd
import geojson
import shapely.wkt
from shapely.geometry import shape, Polygon

from .. import util
from .database import get_db, db_session
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
            if hasattr(geometry, 'to_wkt'):
                geometry = geometry.to_wkt()
            data.update({
                    'name': uri,
                    'collection': collection,
                    'geometry': geometry,
                    })
            db.Feature(**data)
            uris.append(uri)

    return uris


@dispatcher.add_method
def get_features(services=None, collections=None, features=None,
                 expand=False, as_dataframe=False, as_geojson=False,
                 update_cache=False, filters=None):
    """Retrieve list of features from resources

    Args:
        services (comma separated strings, or list of strings, Required):
            list of services to search in for features
        collections (comma separated strings or list of strings):
            list of collections to search in for features
        features (comma separated strings or list of strings, Optional, Default=None):
            list of features to include in search
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

    Returns:
        features (list, geo-json dict or pandas.DataFrame, Default=list):
             features of specified service(s), collection(s) or feature(s)

    """
    if services is None and collections is None and features is None:
        raise ValueError('Specify at least one service, collection or feature')

    services = util.listify(services)
    collections = util.listify(collections)
    features = util.listify(features)

    all_features = []

    # get metadata for directly specified features
    if features is not None:
        all_features.append(get_metadata(features, as_dataframe=True))

    # get metadata for features in services
    for name in services or []:
        provider, service, feature = util.parse_service_uri(name)
        tmp_feats = _get_features(provider, service, update_cache=update_cache)
        all_features.append(tmp_feats)

    # get metadata for features in collections
    db = get_db()
    with db_session:
        for name in collections or []:
            tmp_feats = [f.to_dict() for f in db.Feature.select(
                            lambda c: c.collection.name == name
                        )]
            tmp_feats = gpd.GeoDataFrame(tmp_feats)

            if not tmp_feats.empty:
                tmp_feats['geometry'] = tmp_feats['geometry'].apply(
                                            lambda x: shapely.wkt.loads(x))
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
def new_feature(collection, display_name=None, geom_type=None, geom_coords=None,
                description=None, metadata=None):
    """Add a new feature to a collection.

    Args:
        collection (string, Required):
            name of collection
        display_name (string, Optional, Default=None):
            display name of feature
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

    geometry = None
    if geom_type is not None:
        if geom_type not in ['LineString', 'Point', 'Polygon']:
            raise ValueError(
                    'geom_type must be one of LineString, Point or Polygon'
                )

        if isinstance(geom_coords, str):
            geom_coords = json.loads(geom_coords)

        # convert to wkt using gist
        # https://gist.github.com/drmalex07/5a54fc4f1db06a66679e
        o = {"coordinates": geom_coords, "type": geom_type}
        s = json.dumps(o)
        g1 = geojson.loads(s)
        g2 = shape(g1)
        geometry = g2.wkt

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
