from ..base import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import os
import sys
import platform
import rasterio
import subprocess


class RstMerge(FilterBase):
    def register(self, name='raster-merge'):
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

        # if len(datasets) < 2:
        #     raise ValueError('There must be at LEAST two datasets for this filter')

        orig_metadata = get_metadata(datasets[0])[datasets[0]]
        raster_files = [get_metadata(dataset)[dataset]['file_path'] for dataset in datasets]

        for dataset in datasets:
            if get_metadata(dataset)[dataset]['parameter'] != orig_metadata['parameter']:
                raise ValueError('Parameters must match for all datasets')
            if get_metadata(dataset)[dataset]['unit'] != orig_metadata['unit']:
                raise ValueError('Units must match for all datasets')

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        if options is None:
            options = {}

        if description is None:
            description = 'Raster Filter Applied'

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

        self.file_path = dst

        with rasterio.open(orig_metadata['file_path']) as first_dataset:
            projection = first_dataset.crs
            bands = first_dataset.count

        for file in raster_files:
            if rasterio.open(file).crs != projection:
                raise ValueError('Projections for all datasets must be the same')
            if rasterio.open(file).count != bands:
                raise ValueError('Band count for all datasets must be the same')

        output_vrt = os.path.splitext(dst)[0] + '.vrt'

        subprocess.check_output(['gdalbuildvrt', '-overwrite', output_vrt] + raster_files)

        bbox = options.get('bbox')

        if bbox is not None:
            xmin, xmax, ymin, ymax = bbox

            subprocess.check_output(
                ['gdalwarp', '-overwrite', '-te', str(xmin), str(ymin), str(xmax), str(ymax), output_vrt, dst])

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'unit': orig_metadata['unit']
        }

        # update feature geometry metadata
        with rasterio.open(dst) as f:
            geometry = util.bbox2poly(f.bounds.left, f.bounds.bottom, f.bounds.right, f.bounds.top, as_shapely=True)
        update_metadata(feature, quest_metadata={'geometry': geometry.to_wkt()})

        # update dataset metadata
        new_metadata.update({
            'options': self.options,
            'file_path': self.file_path,
        })
        update_metadata(new_dset, quest_metadata=new_metadata, metadata=metadata)

        return {'datasets': new_dset, 'features': feature}

    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'json-schema':
            properties = {
                "bbox": {
                        "type": "array",
                        "description": "bounding box to clip the merged raster to in the form [xmin, ymin, xmax, ymax]",
                },
            }

            schema = {
                    "title": "Merge Raster Filter",
                    "type": "object",
                    "properties": properties,
                    "required": [],
                }

        if fmt == 'smtk':
            schema = ''

        return schema
