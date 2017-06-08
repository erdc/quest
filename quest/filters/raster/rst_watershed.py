from ..base import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import terrapin
import os
import rasterio
import fiona
import numpy as np
from shapely.geometry import mapping
from shapely.affinity import affine_transform
from terrapin.go_spatial import breach_depressions, fill_depressions, d8_flow_accumulation, fd8_flow_accumulation
from terrapin import snap_points_max_flow_acc, snap_points_jenson
from pyproj import Proj


def write_output(data, metadata, output_file):
    with rasterio.open(output_file, "w", **metadata) as out:
        try:
            out.write(data.astype(metadata['dtype']))
        except ValueError:
            out.write(data.astype(metadata['dtype']), 1)
    return output_file


def read_input(input_file):
    with rasterio.open(input_file) as src:
        data = src.read().squeeze()
        metadata = src.profile
    return data, metadata


# wrapper for terrapin.fill_flats
def fill_flats(input_file, output_file):
    dem, metadata = read_input(input_file)
    d8 = terrapin.d8(dem)
    out_data = terrapin.fill_flats(d8)
    return write_output(out_data, metadata, output_file)


# wrapper for terrapin.d8_flow_accumulation
def flow_accumulation(input_file, output_file):
    dem, metadata = read_input(input_file)
    out_data = terrapin.d8_flow_accumulation(dem)
    return write_output(out_data, metadata, output_file)


# TODO algorithm names need to be changed to something more understandable
FILL_ALGORITHMS = {'go-fill': fill_depressions,
                   # 'go-breach': breach_depressions,  # doesn't work
                   'flats': fill_flats}

ACCUMULATION_ALGORITHMS = {'go-d8': d8_flow_accumulation,
                           'go-fd8': fd8_flow_accumulation,
                           'd8': flow_accumulation}


class RstWatershedDelineation(FilterBase):
    def register(self, name='watershed-delineation'):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'raster',
            'operates_on': {
                'datatype': ['raster'],
                'geotype': None,
                'parameters': None,
            },
            'produces': {
                'datatype': 'raster',
                'geotype': None,
                'parameters': None,
            },
        }

    def _apply_filter(self, datasets, features=None, options=None,
                     display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different services

        orig_metadata = get_metadata(dataset)[dataset]
        collection_name = orig_metadata['collection']
        src_path = orig_metadata['file_path']

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)
        if options is None:
            options ={}

        if description is None:
            description = 'Raster Filter Applied'

        # this filter require a list of outlet points 
        # these can be provided as a list of point features 
        # or a list of outlet points in the options
        if features is not None:
            df = get_metadata(features, as_dataframe=True)
            if not all(df.geometry.type == 'Point'):
                raise ValueError('All the provided features must have the geometry type: Point')
            outlet_points = df.geometry.apply(lambda x: np.array(x.coords).squeeze().tolist()).values.tolist()
        else:
            if not options.get('outlet_points'):
                raise ValueError('Outlet points are required either as input features or in the options')
            outlet_points = np.array(options.get('outlet_points'))
        
        if len(outlet_points) > 1:
            raise NotImplementedError('Filter can currently only take one outlet point')


        # run filter
        with rasterio.open(src_path) as src:
            crs = src.crs
            t = src.transform
            transform = [t.a, t.b, t.d, t.e, t.xoff, t.yoff]

            # Convert outlet points from lat/lon to raster row/col
            # this assumes a list of outlet points in easting, northing
            p = Proj(crs)
            if p.is_latlong():
                proj_points = [src.index(*point) for point in outlet_points]
            else:
                proj_points = [src.index(*p(*point)) for point in outlet_points]

            # read flow accumulation
            flow_accumulation = src.read().squeeze()

            snap = options.get('snap_outlets')
            if snap is not None:
                if snap.lower() == 'maximum_flow_accumulation':
                    proj_points = snap_points_max_flow_acc(flow_accumulation, proj_points, options.get('search_box_pixels'))
                if snap.lower() == 'jenson':
                    stream_threshold_pct = options.get('stream_threshold_pct')
                    stream_threshold_abs = options.get('stream_threshold_abs')
                    outlet_points = snap_points_jenson(flow_accumulation, proj_points, 
                        stream_threshold_pct=stream_threshold_pct, stream_threshold_abs=stream_threshold_abs)
                if p.is_latlong():
                    snapped_points = [src.xy(*point) for point in proj_points]
                else:
                    snapped_points = [src.xy(*p(*point, inverse=True)) for point in proj_points]

                # create new snapped outlet point feature 
                outlet_feature = new_feature(collection_name,
                              display_name=display_name+'_snapped_outlet', geom_type='Point',
                              geom_coords=[snapped_points[0]])
                print('outlet points snapped, new feature created:', snapped_points, outlet_feature)
            else:
                # if input was not a feature then create a feature
                if features is None:
                    outlet_feature = new_feature(collection_name,
                              display_name=display_name+'_outlet', geom_type='Point',
                              geom_coords=[outlet_points[0]])
                    print('outlet points converted to feature, new feature created:', outlet_feature)
                else:
                    outlet_feature = features[0]

            watershed, boundaries = terrapin.d8_watershed_delineation(flow_accumulation, proj_points)
            out_meta = src.profile
            boundary_list = [mapping(affine_transform(boundary, transform)) for boundary in boundaries.values()]

        # Define a polygon feature geometry with one attribute
        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }

        # # save the resulting raster
        out_meta.update(height=watershed.shape[0],
                        width=watershed.shape[1],
                        nodata=-9999)

        feature = new_feature(collection_name,
                              display_name=display_name, geom_type='Polygon',
                              geom_coords=boundary_list[0]['coordinates'])

        new_dset = new_dataset(feature,
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj,  collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        watershed_tif = os.path.join(dst, new_dset+'.tif')
        boundary_polygon = os.path.join(dst, new_dset+'.shp')

        # Write a new Shapefile
        with fiona.open(boundary_polygon, 'w', 'ESRI Shapefile', schema, crs=crs) as c:
            for index, boundary in enumerate(boundary_list):
                c.write({
                    'geometry': boundary,
                    'properties': {'id': index + 1},
                })

        data = watershed.data.astype(out_meta['dtype'])
        data = np.transpose(data)

        # rotate image 90 degrees
        data = np.rot90(data)


        #write out tif file
        with rasterio.open(watershed_tif, 'w', **out_meta) as dest:
            try:
                dest.write(data.astype(out_meta['dtype']))
            except ValueError:
                dest.write(data.astype(out_meta['dtype']), 1)

        self.file_path = watershed_tif

        quest_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata, metadata=metadata)
        return {'datasets': new_dset, 'features': {'watershed':feature, 'outlet':outlet_feature}}


    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'json-schema':
            properties = {
                    "outlet_points": {
                        "type": "string",
                        "description": "Watershed outlet points",
                    },

                }

            schema = {
                    "title": "Watershed Delineation Raster Filter",
                    "type": "object",
                    "properties": properties,
                    "required": ['outlet_points'],
                }

        if fmt == 'smtk':
            schema = ''

        return schema


class RstFlowAccum(FilterBase):
    def register(self, name='flow-accumulation'):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'raster',
            'operates_on': {
                'datatype': ['raster'],
                'geotype': None,
                'parameters': None,
            },
            'produces': {
                'datatype': 'raster',
                'geotype': None,
                'parameters': None,
            },
        }

    def _apply_filter(self, datasets, features=None, options=None,
                      display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different services

        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        if options is None:
            options = {}

        if description is None:
            description = 'Raster Filter Applied'

        # run filter
        with rasterio.open(src_path) as src:
            out_image = terrapin.d8_flow_accumulation(src.read().squeeze())
            out_meta = src.profile

        out_meta.update({"height": out_image.shape[0],
                         "width": out_image.shape[1],
                         "nodata": -9999})

        collection_name = orig_metadata['collection']

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        dst = os.path.join(dst, new_dset + '.tif')

        with rasterio.open(dst, "w", **out_meta) as dest:
            try:
                dest.write(out_image.astype(out_meta['dtype']))
            except ValueError:
                dest.write(out_image.astype(out_meta['dtype']), 1)

        self.file_path = dst

        quest_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata, metadata=metadata)

        return {'datasets': new_dset}

    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'json-schema':
            properties = {}
            schema = {
                "title": "Flow Accumulation Raster Filter",
                "type": "object",
                "properties": properties,
                "required": [],
            }

        if fmt == 'smtk':
            schema = ''

        return schema


class RstFlowAccumulation(FilterBase):
    def register(self, name='flow-accumulation'):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'raster',
            'operates_on': {
                'datatype': ['raster'],
                'geotype': None,
                'parameters': None,
            },
            'produces': {
                'datatype': 'raster',
                'geotype': None,
                'parameters': None,
            },
        }

    def _apply_filter(self, datasets, features=None, options=None,
                      display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different services

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        if options is None:
            options = {}

        options.setdefault('algorithm', 'go-d8')

        if description is None:
            description = 'Raster Filter Applied'

        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        collection_name = orig_metadata['collection']
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        self.file_path = os.path.join(dst, new_dset + '.tif')

        flow_accumulation_algorithm = ACCUMULATION_ALGORITHMS[options['algorithm']]

        # run filter
        flow_accumulation_algorithm(src_path, self.file_path)

        quest_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata, metadata=metadata)

        return {'datasets': new_dset}

    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'json-schema':
            properties = {
                "algorithm": {
                    "type": {"enum": list(ACCUMULATION_ALGORITHMS.keys()), "default": "go-d8"},
                    "description": "algorithm to use for calculating flow accumulation",
                },
            }
            schema = {
                "title": "Flow Accumulation Raster Filter",
                "type": "object",
                "properties": properties,
                "required": ["algorithm"],
            }

        if fmt == 'smtk':
            schema = ''

        return schema


class RstFill(FilterBase):
    def register(self, name='fill'):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'raster',
            'operates_on': {
                'datatype': ['raster'],
                'geotype': None,
                'parameters': None,
            },
            'produces': {
                'datatype': 'raster',
                'geotype': None,
                'parameters': None,
            },
        }

    def _apply_filter(self, datasets, features=None, options=None,
                      display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different services

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        if options is None:
            options = {}

        if description is None:
            description = 'Raster Filter Applied'

        options.setdefault('algorithm', 'go-breach')

        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        collection_name = orig_metadata['collection']
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        self.file_path = os.path.join(dst, new_dset + '.tif')

        fill_algorithm = FILL_ALGORITHMS[options['algorithm']]

        # run filter
        fill_algorithm(src_path, self.file_path)

        quest_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata, metadata=metadata)

        return {'datasets': new_dset}

    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'json-schema':
            properties = {
                "algorithm": {
                    "type": {"enum": list(FILL_ALGORITHMS.keys()), "default": "go-fill"},
                    "description": "algorithm to use for filling the dem",
                },
            }
            schema = {
                "title": "Fill Raster Filter",
                "type": "object",
                "properties": properties,
                "required": ["algorithm"],
            }

        if fmt == 'smtk':
            schema = ''

        return schema

