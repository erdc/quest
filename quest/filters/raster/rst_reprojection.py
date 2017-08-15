from ..base import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import os
import rasterio
import numpy as np
import subprocess


class RstReprojection(FilterBase):
    def register(self, name='raster-reprojection'):
        """Register Raster

        """
        self.name = name
        self.metadata = {
            'group': 'raster',
            'operates_on': {
                'datatype': ['raster','discrete-raster'],
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

        if description is None:
            description = 'Raster Filter Applied'

        if not options.get('new_crs'):
            raise ValueError("A new coordinated reference system MUST be provided")

        dst_crs = options.get('new_crs')

        # # save the resulting raster
        cname = orig_metadata['collection']
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
        extension = os.path.splitext(src_path)[1]
        dst = os.path.join(dst, new_dset + extension)

        # run filter
        with rasterio.open(src_path) as src:
            # write out tif file
            subprocess.check_output(['gdalwarp', src_path, dst, '-s_srs', src.crs.to_string(), '-t_srs', dst_crs])

        self.file_path = dst

        with rasterio.open(dst) as f:
            geometry = util.bbox2poly(f.bounds.left, f.bounds.bottom, f.bounds.right, f.bounds.top, as_shapely=True)
        update_metadata(feature, quest_metadata={'geometry': geometry.to_wkt()})

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
        }

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
            properties = {
                     "new_crs": {
                         "type": "string",
                         "description": "New coordinate reference system to project to",
                     },
                    }

            schema = {
                    "title": "Reprojection Raster Filter",
                    "type": "object",
                    "properties": properties,

                }

        if fmt == 'smtk':
            schema = ''

        return schema
