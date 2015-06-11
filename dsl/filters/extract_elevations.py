"""Extract elevations from raster datasources

"""

from .base import FilterBase
from dsl import api
from .. import util
import geojson
from geojson import Polygon, Feature, FeatureCollection
import pandas as pd
import os
import subprocess

class ExtractElevations(FilterBase):
    def register(self):
        """Register FFD to NRMM Filter

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['raster'],
                'geotype': ['polygon'],
                'parameters': ['elevation'],
                'level': ['collection'],
            },
            'produces': {
                'datatype': 'linestring',
                'geotype': 'line',
                'parameters': ['elevation'],
            },
        }


    def apply_filter(self, collection_name, service=None, method='nearest', input_file=None, **kwargs):
        import rasterio

        # convert service name to service code
        services = api.get_services(parameter='elevation', datatype='raster')
        service = [s['service_code'] for s in services if s['display_name']==service][0]

        # calculate bounding box
        print 'opening geojson file'
        line = geojson.load(open(input_file))
        if line['type'].lower()!='linestring':
            print 'Please enter a GeoJSON formatted as a LineString'
            return

        coords = line['coordinates']
        polygon = Polygon([coords + list(reversed(coords))[1:]])
        coords = pd.DataFrame(coords, columns=['lon','lat'])

        buf = 0.0001
        bbox = [coords.lon.min()-buf, coords.lat.min()-buf, coords.lon.max()+buf, coords.lat.max()+buf]
        print 'calculated bounding box: ', str(bbox)

        # identify and download the required raster tiles
        print 'downloading required tiles'
        locs = api.get_locations(service, bounding_box=bbox)
        locs = [loc['id'] for loc in locs['features']]
        if len(locs)==0:
            print 'no tiles found'
            return
            
        tiles = api.get_data(service, locs)
        tiles = [v['elevation'] for v in tiles.values()]

        if len(tiles)>1:
            raster = os.path.splitext(tiles[0])[0] + '.vrt'
            print subprocess.check_output(['gdalbuildvrt', '-overwrite', raster] + tiles)
        else:
            raster = tiles[0]

        print 'extracting elevations along path'
        with rasterio.drivers():
            with rasterio.open(raster) as src:
                if method=='nearest':
                    elevations = list(src.sample(line['coordinates']))
                    coords = [xy + z.tolist() for xy, z in zip(line['coordinates'], elevations)]
                elif method=='bilinear':
                    coords = []
                    for x,y in line['coordinates']:
                        a, b, c, d, e, f, _, _, _ = src.affine
                        yf, r = math.modf((y-f)/e)
                        xf, c = math.modf((x-c)/a)
                        r, c = int(r), int(c)
                        window = ((r, r+2), (c, c+2))
                        data = src.read(None, window=window, masked=False, boundless=True)
                        q11, q21, q12, q22 = data[0,0,0], data[0,0,1], data[0,1,0], data[0,1,1]
                        z = (1-yf)*((1-xf)*q11 + xf*q21) + yf*((1-xf)*q12 + xf*q22)
                        coords.append([x, y, z.tolist()])

        line['coordinates'] = coords

        #save GeoJSON to an output file and add to collection
        collection = api.get_collection(collection_name)

        plugin_dir = os.path.join(collection['path'], 'elevations_along_path')
        util.mkdir_if_doesnt_exist(plugin_dir)
        head, tail = os.path.split(input_file)
        fname, ext = os.path.splitext(tail)
        fname = fname + '_with_elevations_from_%s' % service + ext
        filename = os.path.join(plugin_dir, fname)
        print 'saving output GeoJSON to %s' % filename
        with open(filename, 'w') as f:
            f.write(geojson.dumps(line))

        properties = {
            'metadata': 'generated using get_elevations_along_path plugin', 
            'input_file': input_file,
            'elevation_service': service,
            'relative_path': filename, 
            'datatype': 'linestring'
        }

        new_locs = FeatureCollection([Feature(geometry=polygon, properties=properties, id=hash(str(line)))])
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