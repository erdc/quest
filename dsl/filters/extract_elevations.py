"""Extract elevations from raster datasources

DEPRECIATED .... NOT CURRENTLY WORKING WITH NEW API

"""
from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import zip
from past.utils import old_div

from affine import Affine
from .base import FilterBase
from dsl import api
from .. import util
import geojson
from geojson import Polygon, Feature, FeatureCollection
import math
import numpy as np
import pandas as pd
import os
import subprocess
import uuid


class ExtractElevations(FilterBase):
    def register(self):
        """Register FFD to NRMM Filter

        """
        self.schema = {}

        self.metadata = {
            'group': 'Raster',
            'operates_on': {
                'datatype': 'raster',
                'geotype': 'Polygon',
                'parameters': ['elevation'],
            },
            'produces': {
                'datatype': 'linestring',
                'geotype': 'LineString',
                'parameters': ['elevation'],
            },
        }


    def apply_filter(self, collection_name, service=None, method='nearest', input_file=None, output_file=None, **kwargs):
        import rasterio
        import rasterio.features
        import fiona

        services = api.get_services(parameter='elevation', datatype='raster')
        # convert service name to service code (for DataBrowser since it displays Service Display Name)
        if service not in [s['service_code'] for s in services]:
            service = [s['service_code'] for s in services if s['display_name']==service][0]

        #setup output file
        collection = api.get_collection(collection_name)
        plugin_dir = os.path.join(collection['path'], 'elevations_along_path')
        util.mkdir_if_doesnt_exist(plugin_dir)
        head, tail = os.path.split(input_file)
        fname, ext = os.path.splitext(tail)
        fname = fname + '_with_elevations_from_%s' % service + ext
        if output_file is None:
            filename = os.path.join(plugin_dir, fname)
        else:
            filename = output_file

        # read vector features
        with fiona.open(input_file, 'r') as vector:
            # identify and download the required raster tiles
            bbox = list(vector.bounds)
            x1, y1, x2, y2 = bbox
            polygon = Polygon([_bbox2poly(x1, y1, x2, y2)])

            print('downloading required tiles')
            locs = api.get_locations(service, bounding_box=bbox)
            locs = [loc['id'] for loc in locs['features']]
            if len(locs)==0:
                print('no tiles found')
                return

            tiles = api.get_data(service, locs)
            tiles = [v['elevation'] for v in list(tiles.values())]

            if len(tiles)>1:
                raster_file = os.path.splitext(tiles[0])[0] + '.vrt'
                print(subprocess.check_output(['gdalbuildvrt', '-overwrite', raster_file] + tiles))
            else:
                raster_file = tiles[0]

            print('extracting elevations along feature')
            with rasterio.drivers():
                with rasterio.open(raster_file, 'r') as raster:
                    masks = []
                    if os.path.isfile(filename):
                        os.remove(filename) #fiona can't write to an existing file
                    with fiona.open(filename,'w',driver=vector.driver, crs=vector.crs, schema=vector.schema) as output:
                        for feature in vector:
                            points = feature['geometry']['coordinates']
                            masks.append((feature['geometry'], 0))
                            if method=='nearest':
                                elevations = list(raster.sample(points))
                                coordinates = [xy + tuple(z.tolist()) for xy, z in zip(points, elevations)]
                            elif method=='bilinear':
                                coordinates = []
                                for x,y in points:
                                    a, b, c, d, e, f, _, _, _ = raster.affine
                                    yf, r = math.modf(old_div((y-f),e))
                                    xf, c = math.modf(old_div((x-c),a))
                                    r, c = int(r), int(c)
                                    window = ((r, r+2), (c, c+2))
                                    data = raster.read(None, window=window, masked=False, boundless=True)
                                    q00, q01, q10, q11 = data[0,0,0], data[0,1,0], data[0,0,1], data[0,1,1]
                                    z = (1-yf)*((1-xf)*q00 + xf*q10) + yf*((1-xf)*q01 + xf*q11)
                                    coordinates.append((x, y, z))

                            feature['geometry']['coordinates'] = coordinates
                            output.write(feature)

                    # create visualization
                    ul = raster.index(bbox[0], bbox[1])
                    lr = raster.index(bbox[2], bbox[3])
                    window = ((lr[0], ul[0]+1), (ul[1], lr[1]+1))
                    data = raster.read(1, window=window)
                    t = raster.affine
                    shifted_affine = Affine(t.a, t.b, t.c+ul[1]*t.a, t.d, t.e, t.f+lr[0]*t.e)
                    mask = rasterio.features.rasterize(masks, out_shape=data.shape, transform=shifted_affine, fill=1, all_touched=True, dtype=np.uint8)
                    masked_data = np.ma.array(data=data, mask=mask.astype(bool))
                    kwargs = raster.meta
                    kwargs['transform'] = shifted_affine
                    kwargs['affine'] = shifted_affine
                    kwargs['driver'] = 'GTIFF'
                    kwargs['width'] = masked_data.shape[1]
                    kwargs['height'] = masked_data.shape[0]
                    view_file = filename.split('.')[0] + '.tif'
                    with rasterio.open(view_file, 'w', **kwargs) as dst:
                        dst.write_band(1, masked_data.filled(fill_value=kwargs['nodata']))

            print('saving output to %s' % filename)

        properties = {
            'metadata': 'generated using get_elevations_along_path plugin',
            'input_file': input_file,
            'elevation_service': service,
            'relative_path': filename,
            'view': view_file,
            'datatype': 'vector',
        }

        new_locs = FeatureCollection([Feature(geometry=polygon, properties=properties, id=str(uuid.uuid4()))])
        collection = api.add_to_collection(collection_name, 'local', new_locs, parameters='elevation')
        return collection

    def apply_filter_options(self, **kwargs):
        services = api.get_services(parameter='elevation', datatype='raster')
        services = [svc['display_name'] for svc in services]
        properties = {
            "input_file": {
                "type": "string",
                "description": "Complete File Path to GeoJSON file defining path",
            },
            "service": {
                "type": { "enum": services, "default": services[0] },
                "description": "Elevation Dataset to use for extraction",
            },
            "method": {
                "type": { "enum": ['nearest', 'bilinear'], "default": 'nearest'},
                "description": "Type of interpolation to use in extraction from raster",
            },
        }

        schema = {
            "title": "Download Elevations along Path",
            "type": "object",
            "properties": properties,
            "required": ["input_file", "service", 'method'],
        }

        return schema


def _bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly
