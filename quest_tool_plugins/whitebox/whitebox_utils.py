import os
import re
import time
import logging
import inspect
from functools import wraps

import rasterio
import numpy as np
import xarray as xr
import pandas as pd
import whitebox_tools
import geopandas as gpd
from shapely.geometry import Point, shape

from quest.static import DataType
from quest.util import listify, convert_nodata_to_nans


whitebox_log = logging.getLogger('whitebox')
whitebox_log.addHandler(logging.NullHandler())
whitebox_log.propagate = True
whitebox_temp_dir = os.environ.get('WHITEBOX_TOOLS_DIR') or os.path.expanduser('~/.whitebox_tools_tempdir')
os.makedirs(whitebox_temp_dir, exist_ok=True)
whitebox_log.addHandler(logging.FileHandler(os.path.join(whitebox_temp_dir, 'whitebox.log')))


def data_array_to_rasterio(xr_data, output_file=None, tag=None, fmt='GTiff', metadata=None):
    """Write xarray DataArray to file using rasterio.
    """
    extensions = {
        'GTiff': '.tif',
    }
    output_file = output_file or os.path.join(whitebox_temp_dir, str(tag) + extensions[fmt])
    metadata = metadata or dict()

    shape = xr_data.shape
    if len(shape) == 2:
        shape = (1, *shape)

    count, height, width = shape
    bands = 1 if count == 1 else np.arange(count) + 1

    metadata.update(
        driver=fmt,
        height=height,
        width=width,
        dtype=str(xr_data.dtype),
        count=count,
    )

    if 'transform' in xr_data.attrs:
        metadata['transform'] = rasterio.Affine(*xr_data.attrs['transform'][:6])

    if 'crs' in xr_data.attrs:
        metadata['crs'] = rasterio.crs.CRS.from_string(xr_data.attrs['crs'])

    with rasterio.open(output_file, 'w', **metadata) as output:
        output.write(xr_data.values.astype(metadata['dtype']), bands)

    return output_file


def tif_to_data_array(path, with_nans=True):
    """Read in a tif file to an xarray DataArray and replace nodata values with Nan
    """
    output = xr.open_rasterio(path, parse_coordinates=True).isel(band=0)
    if with_nans:
        output = convert_nodata_to_nans(output)
    return output


def points_to_shp(points, shp_file=None):
    """Take a list of coordinates or Shapely Point objects and write them to a ShapeFile.
    """
    points = listify(points)
    test_point = points[0]
    if isinstance(test_point, Point):
        pts = points
    elif isinstance(test_point, list) or isinstance(test_point, tuple):
        pts = [Point(*xy) for xy in points]
    elif isinstance(test_point, float) or isinstance(test_point, int):
        pts = [Point(points)]

    shp_file = shp_file or os.path.join(whitebox_temp_dir, '{}_{}.{}'.format('point', time.time(), 'shp'))
    gdf = gpd.GeoDataFrame(geometry=pts)
    gdf.to_file(shp_file)
    return shp_file


def raster_to_polygons(raster_file):
    with rasterio.open(raster_file) as src:
        image = src.read(1)  # first band
        mask = src.read_masks(1)
        results = (
            {'index': v, 'geometry': shape(s).buffer(0)} for s, v in
            rasterio.features.shapes(image, mask=mask, connectivity=8, transform=src.transform))

    df = gpd.GeoDataFrame(results)
    df.set_index('index', drop=True, inplace=True)

    return df


def default_callback(msg):
    """Default message handeling function to log whitebox_tools output.
    """
    whitebox_log.log(logging.INFO, msg)


def get_output_path(row):
    """Create the name for an output argument from a Pandas DataFrame row.
    """
    return os.path.join(whitebox_temp_dir, '{}_{}_{}.{}'.format(row.tool, row.arg_name, time.time(), row.output_type))


def classify_output(doc):
    """Determine the type of output for an argument based on the docstring.
    """
    if doc.find('raster') > 0 or doc.find('colour') > 0:
        return 'tif'
    if doc.find('HTML') > 0:
        return 'html'
    if doc.find('LiDAR') > 0:
        return 'lidar'


def get_required_outputs_with_defaults(tool):
    """Parse the doc string for a whitebox tool and return a dictionary of the
    positional output arguments with default values.
    """
    parameters = inspect.signature(tool).parameters
    required_args = set([p.name for p in parameters.values() if p.default == p.empty])
    docs = {k: v.strip() for k, v in re.findall('^\s*(.*) -- (.*)', tool.__doc__, re.MULTILINE)}

    df = pd.DataFrame([
        {'tool': tool.__name__, 'arg_name': k, 'doc': v}
        for k, v in docs.items()
        if k in required_args and v.startswith('Output')]
    )

    df['output_type'] = df.doc.apply(classify_output)
    df['file_path'] = df.apply(get_output_path, axis=1)

    kwargs = dict()
    for index, row in df.iterrows():
        kwargs[row.arg_name] = row.file_path

    return kwargs


def args_to_kwargs(tool, args):
    """Use inspection to convert a list of args to a dictionary of kwargs.
    """
    argnames = list(inspect.signature(tool).parameters.keys())[1:]  # get list of argsnames and remove self
    kwargs = {argnames[i]: arg for i, arg in enumerate(args)}
    return kwargs


def whitebox_tools_wrapper(tool):
    """Decorator to pre- and post-process arguments for whitebox tools. Converts all xarray DataArray inputs to
    file path inputs. Also, provides default values for all required outputs, and reads them back in as
    xarray DataArrays.
    """

    @wraps(tool)
    def wrapped(self, *args, **kwargs):
        required_outputs = get_required_outputs_with_defaults(tool)
        all_kwargs = dict(required_outputs)
        all_kwargs.update(callback=default_callback)

        kwargs.update(args_to_kwargs(tool, args))
        for k, v in kwargs.items():
            if isinstance(v, xr.DataArray):
                kwargs[k] = data_array_to_rasterio(v, tag=k)

        all_kwargs.update(kwargs)

        tool(self, **all_kwargs)

        result = list()
        for output in required_outputs.keys():
            path = all_kwargs[output]
            try:
                result.append(tif_to_data_array(path))
            except Exception as e:
                whitebox_log.log(logging.ERROR, e)
                raise
        if len(result) == 1:
            result = result[0]

        return result

    return wrapped


wbt = whitebox_tools.WhiteboxTools()

try:
    whitebox_tools_has_been_wrapped
except NameError:
    for tool in wbt.list_tools().keys():
        try:
            setattr(whitebox_tools.WhiteboxTools,
                    tool,
                    whitebox_tools_wrapper(getattr(whitebox_tools.WhiteboxTools, tool))
                    )
        except AttributeError:
            pass
            # skip the following tools because they are not valid attributes in the python wrapping:
            #         and
            #         corner_detection
            #         lidar_thin
            #         not
            #         or
            #         unsharp_masking
            #         weighted_overlay
    whitebox_tools_has_been_wrapped = True
