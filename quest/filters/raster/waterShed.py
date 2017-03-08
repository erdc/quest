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

class RstWaterShed(FilterBase):
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

        if not options:
            raise ValueError('Outlet points are required')

        x,y = options.get('outlet_points')
        outlet_points = list(zip(x,y))
        # run filter
        with rasterio.open(src_path) as src:
            watershed, boundary = terrapin.d8_watershed_delineation(src.read().squeeze(), outlet_points)
            out_meta = src.profile

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
        with fiona.open(boundary_polygon, 'w', 'ESRI Shapefile', schema) as c:
            ## If there are multiple geometries, put the "for" loop here
            c.write({
                'geometry': mapping(boundary[1]),
                'properties': {'id': 123},
            })

        data = watershed.data.astype(out_meta['dtype'])
        data = np.transpose(data)

        # rotate image 90 degrees
        data = np.rot90(data)


        #write out tif file
        with rasterio.open(watershed_tif, 'w', **out_meta) as src:
                src.write(data, 1)

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
        schema = {}
        # # if fmt == 'json-schema':
        properties = {
                "bbox": {
                    "type": "string",
                    "description": "bounding box 'xmin, ymin, xmax, ymax'",
                },
                "nodata": {
                    "type": "number",
                    "description": "no data value for raster.",
                    "default": 0,
                },
            }

        schema = {
                "title": "Raster Watershed Delineation",
                "type": "object",
                "properties": properties,
                "required": ['outlet_points'],
            }
        #
        # if fmt == 'smtk':
        #     schema = ''
        #
        return schema

    # def _apply(df, metadata, options):
    #     raise NotImplementedError

