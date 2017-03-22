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

class RstDelineation(FilterBase):
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
        src_path = orig_metadata['file_path']
        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)
        if options is None:
            options ={}

        if not options.get('outlet_points'):
            raise ValueError('Outlet points are required')

        outlet_points = options.get('outlet_points')

        # run filter
        with rasterio.open(src_path) as src:
            crs = src.crs
            t = src.transform
            transform = [t.a, t.b, t.d, t.e, t.xoff, t.yoff]
            watershed, boundaries = terrapin.d8_watershed_delineation(src.read().squeeze(), outlet_points)
            out_meta = src.profile
            boundary_list = [mapping(affine_transform(boundary, transform)) for boundary in boundaries.values()]

        # Define a polygon feature geometry with one attribute
        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }


        # # save the resulting raster
        out_meta.update(height=watershed.shape[0], width=watershed.shape[1])
        cname = orig_metadata['collection']#lakenya replaced
        feature = new_feature(cname,
                              display_name=display_name, geom_type='Polygon',
                              geom_coords=None)

        new_dset = new_dataset(feature,
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj,  cname, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        watershed_tif = os.path.join(dst, new_dset+'.tif')
        boundary_polygon = os.path.join(dst,new_dset+'.shp')

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

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
        }

        if description is None:
            description = 'Raster Filter Applied'

        # update metadata
        new_metadata.update({
            'options': self.options,
            'file_path': self.file_path,
        })
        update_metadata(new_dset, quest_metadata=new_metadata, metadata=metadata)

        return {'datasets': new_dset, 'features': feature}

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

    # def _apply(df, metadata, options):
    #     raise NotImplementedError

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

        # run filter
        with rasterio.open(src_path) as src:
            out_image = terrapin.d8_flow_accumulation(src.read().squeeze())
            out_meta = src.profile

        out_meta.update({"height": out_image.shape[0],
                         "width": out_image.shape[1],
                         "transform": None})

        cname = orig_metadata['collection']
        feature = new_feature(cname,
                              display_name=display_name, geom_type='Polygon',
                              geom_coords=None)

        new_dset = new_dataset(feature,
                               source='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, cname, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        dst = os.path.join(dst, new_dset + '.tif')

        with rasterio.open(dst, "w", **out_meta) as dest:
            try:
                dest.write(out_image.astype(out_meta['dtype']))
            except ValueError:
                dest.write(out_image.astype(out_meta['dtype']), 1)

        self.file_path = dst

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
        }

        if description is None:
            description = 'Raster Filter Applied'

        # update metadata
        new_metadata.update({
            'options': self.options,
            'file_path': self.file_path,
        })
        update_metadata(new_dset, quest_metadata=new_metadata, metadata=metadata)

        return {'datasets': new_dset, 'features': feature}

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

    def _apply(df, metadata, options):
        raise NotImplementedError
