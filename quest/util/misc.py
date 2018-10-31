import os
import re
import warnings
from uuid import uuid4, UUID

import shapely.geometry
import geopandas as gpd
import pandas as pd
import numpy as np
from geojson import LineString, Point, Polygon, Feature, FeatureCollection, MultiPolygon

try:
    import simplejson as json
except ImportError:
    import json

from .config import get_settings
from ..static import UriType


def _abs_path(path, mkdir=True):
    """Gets the absolute path for a file to be within the Quest directory,
       and will create a directory of that filename.

    Args:
        path (string): A string that is a filename.
        mkdir (bool): A boolean if the user wants to create the directory.
    Returns:
        A string of an absolute path with a file from somewhere with in the Quest directory.
    """

    if not os.path.isabs(path):
        path = os.path.join(get_quest_dir(), path)

    if mkdir:
        os.makedirs(path, exist_ok=True)

    return path


def bbox2poly(x1, y1, x2, y2, reverse_order=False, as_geojson=False, as_shapely=False):
    """Converts a bounding box to a polygon.

    Args:
        x1 (int): An int for the first x coordinate.
        y1 (int): An int for the first y coordinate.
        x2 (int): An int for the second x coordinate.
        y2 (int): An int for the second y coordinate.
        reverse_order (bool): A boolean to switch the order of the x and y coordinates.
        as_geojson (bool): A bool to convert the polygon to a geojson object.
        as_shapely (bool): A bool to convert the polygon to a shapely object.

    Returns:
        If the bool is false for both geojson and shapely then just a list is returned.
        If the bool is true for both geojson and shapely then a shapley object is returned.
        If the bool is true for just the geojson, then a geojson object is returned.
        If the bool is true for just the shapely, then a shapely object is returned.
    """
    if reverse_order:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    xmin, xmax = [float(x1), float(x2)]
    ymin, ymax = [float(y1), float(y2)]

    poly = list([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin]])
    poly.append(poly[0])

    if not (as_geojson or as_shapely):
        return poly

    if as_geojson:
        polygon = Polygon
        multi_polygon = MultiPolygon

    if as_shapely:
        polygon = shapely.geometry.Polygon
        multi_polygon = shapely.geometry.MultiPolygon

    xmin2 = xmax2 = None
    if xmin < -180:
        xmin2 = 360 + xmin
        xmin = -180
    if xmax > 180:
        xmax2 = xmax - 360
        xmax = 180

    if xmin2 is None and xmax2 is None:
        return polygon(poly)
    # else bbox spans 180 longitude so create multipolygon

    poly1 = list([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin]])
    poly1.append(poly1[0])

    xmin = xmin2 or -180
    xmax = xmax2 or 180

    poly2 = list([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin]])
    poly2.append(poly2[0])

    return multi_polygon(polygons=[polygon(poly1), polygon(poly2)])


def classify_uris(uris, grouped=True, as_dataframe=True, require_same_type=False, exclude=None, raise_if_empty=True):
    """Converts a list of uris into a pandas dataframe.

    Notes:
        Classified by resource type.

    Args:
        uris (list or string): List of Quest uris to classify into the following types: 'collections', 'services',
        'publishers', or 'datasets'.
        grouped (bool): If True returns
        Pandas GroupBy object (see: https://pandas.pydata.org/pandas-docs/stable/groupby.html)
        as_dataframe (bool): If True returns a Pandas DataFrame
        require_same_type (bool): If True raises a `ValueError` if uris of more than one type are passed in.
        exclude (list or string): List of uri types to not allow. If a uri of an excluded type is passed in
        then a `ValueError` will be raised.

    Returns:
        A pandas dataframe.
    """
    uris = listify(uris)

    df = pd.DataFrame(uris, columns=['uri'])
    df['type'] = UriType.COLLECTION

    uuid_idx = df['uri'].apply(is_uuid)
    service_idx = df['uri'].str.startswith('svc://')
    publish_idx = df['uri'].str.startswith('pub://')
    dataset_idx = uuid_idx & df['uri'].str.startswith('d')

    df['type'][service_idx] = UriType.SERVICE
    df['type'][publish_idx] = UriType.PUBLISHER
    df['type'][dataset_idx] = UriType.DATASET
    df.set_index('uri', drop=False, inplace=True)

    grouped_df = df.groupby('type')

    if raise_if_empty:
        if df.empty:
            raise ValueError('At least one uri must be specified.')

    if exclude is not None:
        for uri_type in exclude:
            if uri_type in grouped_df.groups:
                raise ValueError('Uris for {0} are not allowed.'.format(uri_type))

    if require_same_type and len(grouped_df.groups.keys()) > 1:
        raise ValueError('All uris must be of the same type')

    if not as_dataframe:
        groups = {k: list(v) for k, v in grouped_df.groups.items()}
        return groups

    if grouped:
        return grouped_df

    return df


def construct_service_uri(provider, service, catalog_id=None):
    """Builds a uri from the given parameters.

    Args:
        provider (string): A string of the provider.
        service (string): A string of the service.
        catalog_id (string): A string of the catalog_id.

    Returns:
        If there is no catalog_id then the uri will just be the provider
        and service, else the catalog_id will be appended to the end of the
        uri.
    """
    uri = 'svc://{}:{}'.format(provider, service)
    if catalog_id is not None:
        uri = '{}/{}'.format(uri, catalog_id)

    return uri


def convert_nodata_to_nans(xarr):
    """

    Args:
        xarr:

    Returns:

    """
    nodata_attr = [k for k in xarr.attrs.keys() if k.lower().startswith('nodata')][0]
    nodata = xarr.attrs[nodata_attr]
    if nodata:
        if str(xarr.dtype).startswith('int') or str(xarr.dtype).startswith('uint'):
            xarr.values = xarr.values.astype(np.float32)
        xarr.values[xarr.values == nodata] = np.nan
    return xarr


def get_cache_dir(service=None):
    """Gets the absolute path of the cached directory.

    Args:
        service (string): A string of the specific service the user wants.

    Returns:
        A string of the path to the cached directory.
    """
    settings = get_settings()
    path = _abs_path(settings['CACHE_DIR'])

    if service is not None:
        path = os.path.join(path, service)

    return path


def get_projects_dir():
    """Gets the absolute path of the projects directory within Quest.

    Returns:
        An absolute path leading to the project directory from within Quest.
    """
    settings = get_settings()
    return _abs_path(settings['PROJECTS_DIR'], mkdir=False)


def get_quest_dir():
    """Gets the absolute path of the Quest directory.

    Returns:
        An absolute path of the Quest directory.
    """
    settings = get_settings()
    return settings['BASE_DIR']


def is_remote_uri(path):
    """Checks if the incoming path is a remote uri.

    Args:
        path (string): A string that is either a path or uri.

    Returns:
        If the path is a remote destination then true, false otherwise.
    """
    return bool(re.search('^https?\://', path))


def is_uuid(uuid):
    """Check if string is a uuid4.

    Notes:
        source: https://gist.github.com/ShawnMilo/7777304

    Args:
        uuid (int): A universal unique identifier.

    Returns:
        If the uuid is version 4 then true, else false otherwise.
    """
    try:
        val = UUID(uuid, version=4)
    except ValueError:
        # If it's a value error, then the string is not a valid UUID.
        return False

    # If the uuid_string is a valid hex code, but an invalid uuid4,
    # the UUID.__init__ will convert it to a valid uuid4.
    # This is bad for validation purposes.
    return val.hex == uuid


def listify(liststr, delimiter=','):
    """Converts a string into a list.

    Args:
        liststr (string): A string of words or etc.
        delimiter (char): A char that will be used as the delimiter identifier.

    Returns:
        If a string then a string will be a list.
        If nothing is sent in, then none will be returned.
        If a list, then a list will be returned.
        If not a list or string, then the item will be returned.
    """
    if liststr is None:
        return None

    if isinstance(liststr, (tuple, list, set, dict)):
        return liststr
    elif isinstance(liststr, str):
        return [s.strip() for s in liststr.split(delimiter)]
    else:
        return [liststr]


def parse_service_uri(uri):
    """Parses a service uri into separate provider, service, and catalog_id strings.

    Examples:
        usgs-nwis:dv/0800345522
        gebco-bathymetry
        usgs-ned:1-arc-second

    Args:
        uri (string): A string that is a uri.

    Returns:
        Three strings are returned from the parsed uri.
    """
    svc, catalog_id = (uri.split('://')[-1].split('/', 1) + [None])[:2]
    provider, service = (svc.split(':') + [None])[:2]

    return provider, service, catalog_id


def setattr_on_dataframe(df, attr, value, warnings_filter='ignore'):
    with warnings.catch_warnings():
        warnings.simplefilter(warnings_filter)
        setattr(df, attr, value)


def to_geodataframe(feature_collection):
    """Converts a dictionary to a GeoPandas Dataframe object.

    Args:
        feature_collection (dictionary): A dictionary that contains features.

    Returns:
        A GeoPandas Dataframe.
    """
    features = {}
    for feature in feature_collection['features']:
        data = feature['properties']
        data.update({
            'service_id': feature['id'],
            'geometry': shapely.geometry.shape(feature['geometry'])
        })

        features[feature['id']] = data
    return gpd.GeoDataFrame.from_dict(features, orient='index')


def to_geojson(df):
    """Converts a dataframe to a geojson object.

    Args:
        df (dataframe): A dataframe that is being converted to a geojson object.

    Returns:
        A geojson object is what is being returned.
    """
    _func = {
        'LineString': LineString,
        'Point': Point,
        'Polygon': Polygon,
    }
    features = []
    if not df.empty:
        # TODO what is this code doing and is it now obsolete with the new DB?
        idx = df.columns.str.startswith('_')
        r = {field: field[1:] for field in df.columns[idx]}
        for uid, row in df.iterrows():
            metadata = json.loads(row[~idx].dropna().to_json())
            row = row[idx].rename(index=r)

            # create geojson geometry
            geometry = None
            if row['geom_type'] is not None:
                coords = row['geom_coords']
                if not isinstance(coords, (list, tuple)):
                    coords = json.loads(coords)
                geometry = _func[row['geom_type']](coords)
            del row['geom_type']
            del row['geom_coords']

            # split fields into properties and metadata
            properties = json.loads(row.dropna().to_json())
            properties.update({'metadata': metadata})
            features.append(Feature(geometry=geometry, properties=properties,
                                    id=uid))

    return FeatureCollection(features)


def to_json_default_handler(obj):
    """Gets an attribute from the object.

    Notes:
        This method is confusing and the name is confusing.

    Args:
        obj (object): An object of some nature.

    Returns:
        If the object has an attribute isoformat, then return it.
    """
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()


def uuid(resource_type):
    """Generate a new uuid.

    Notes:
        First character of uuid is replaced with 'd' for resource_type dataset.

    Args:
        resource_type (string): A string that is a type of resource i.e. 'dataset'.

    Returns:
        A new uuid from the resource type.
    """
    uuid = uuid4().hex

    if resource_type == 'dataset':
        uuid = 'd' + uuid[1:]

    return uuid

