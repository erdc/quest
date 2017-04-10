from ..base import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import os
import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling


class RstReproj(FilterBase):
    def register(self, name='reprojection'):
        """Register Raster

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


        if description is None:
            description = 'Raster Filter Applied'

        dst_crs = options.get('new_crs')
        # run filter
        with rasterio.open(src_path) as src:
            profile = src.profile

            dst_transform, dst_width, dst_height = rasterio.warp.calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)

            destination = np.empty(src.shape)
            rasterio.warp.reproject(source=src.read(), destination=destination, src_transform=src.transform, src_crs=src.crs, dst_transform=src.transform, dst_crs=dst_crs, resampling=rasterio.warp.Resampling.nearest)

            # Update destination profile
            profile.update({
                "crs": dst_crs,
                "transform": dst_transform,
            })


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
        dst = os.path.join(dst, new_dset+'.tif')

        #write out tif file
        with rasterio.open(dst, 'w', **profile) as dest:
            dest.write(destination.astype(profile["dtype"]),1)

        self.file_path = dst

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
            properties = {
                    },

            schema = {
                    "title": "Reprojection Raster Filter",
                    "type": "object",
                    "properties": properties,

                }

        if fmt == 'smtk':
            schema = ''

        return schema
