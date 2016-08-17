"""Functions required run raster filters"""
from ..base import FilterBase
from dsl import util

from dsl.api import get_metadata, new_dataset, update_metadata, new_feature
from dsl.api.projects import active_db

import os
import rasterio
from rasterio.tools.mask import mask

class RasterClip(FilterBase):
    def register(self, name=None):
        """Register Timeseries

        """
        self.name = 'raster-clip'
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


    def apply_filter(self, datasets, features=None, options=None,
                     display_name=None, description=None, metadata=None):

        datasets = util.listify(datasets)

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different services
        dataset = datasets[0]
        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['_save_path']
        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        # the polygon GeoJSON geometry
        bbox = options.get('bbox')
        poly = [util.bbox2poly(*util.listify(bbox))]
        geoms = [{'type': 'Polygon', 'coordinates': poly}]

        # load the raster, mask it by the polygon and crop it
        with rasterio.open(src_path) as src:
            out_image, out_transform = mask(src, geoms, crop=True)

        out_meta = src.meta.copy()
        nodata = options.get('nodata', 0)
        out_meta.update({'nodata': nodata})

        # save the resulting raster
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        cname = orig_metadata['_collection']
        feature = new_feature(cname,
                              display_name=display_name, geom_type='Polygon',
                              geom_coords=poly)

        new_dset = new_dataset(feature,
                               dataset_type='derived',
                               display_name=display_name,
                               description=description)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, cname, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        dst = os.path.join(dst, new_dset+'.tif')

        with rasterio.open(dst, "w", **out_meta) as dest:
            dest.write(out_image)

        self.save_path = dst

        new_metadata = {
            'parameter': orig_metadata['_parameter'],
            'datatype': orig_metadata['_datatype'],
            'file_format': orig_metadata['_file_format'],
        }

        if description is None:
            description = 'raster-clip filter applied'

        # update metadata
        new_metadata.update({
            'filter_applied': self.name,
            'filter_options': options,
            'parent_datasets': ','.join(datasets),
            'save_path': self.save_path,
        })
        update_metadata(new_dset, dsl_metadata=new_metadata, metadata=metadata)

        return {'datasets': new_dset, 'features': feature}

    def apply_filter_options(self, fmt='json-schema'):
        if fmt == 'json-schema':
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
                "title": "Raster Clip",
                "type": "object",
                "properties": properties,
                "required": ['bbox'],
            }

        if fmt == 'smtk':
            schema = ''

        return schema
