from ..base import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import terrapin
import os
import rasterio
from pyproj import Proj
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

        orig_meta = {k:get_metadata(k)[k] for k in datasets}
        raster_files = [get_metadata(dataset)[dataset]['file_path'] for dataset in datasets]

        if display_name is None:
            display_name = 'Created by filter {}'.format(self.name)

        if options is None:
            options = {}
        #
        # if not options.get('x_min') or not options.get('y_min')or not options.get('x_max')or not options.get('_max') or not options.get('output_path'):
        #     raise ValueError('x_min, y_min, x_max, y_max and output_path are required')

        xmin = options.get('x_min')
        ymin = options.get('y_min')
        xmax = options.get('x_max')
        ymax = options.get('y_max')
        output_path = options.get('output_path')

        base_path = os.environ["PYTHONPATH"].split(os.pathsep)
        base_path = base_path[0]
        print('Mosaic and clip to bounding box extents')
        output_vrt = os.path.splitext(output_path)[0] + '.vrt'
        gdal_build_vrt = os.path.join(base_path,'gdalbuildvrt')
        gdal_warp = os.path.join(base_path,'gdalwarp')
        print(subprocess.check_output([gdal_build_vrt, '-overwrite', '-allow_projection_difference',output_vrt] + raster_files))
        # check crs
        with rasterio.Env():
            with rasterio.open(output_vrt) as src:
                p = Proj(src.crs)

        p = p.to_latlong()
        if not p.is_latlong():
            [xmax, xmin], [ymax, ymin] = p([xmax, xmin], [ymax, ymin])

        print(subprocess.check_output(
            [gdal_warp, '-overwrite', '-te', repr(xmin), repr(ymin), repr(xmax), repr(ymax), output_vrt, output_path]))
        print('Output raster saved at %s', output_path)


        # # save the resulting raster
        # out_meta.update(height=watershed.shape[0], width=watershed.shape[1])
        # cname = orig_metadata['collection']
        # feature = new_feature(cname,
        #                       display_name=display_name, geom_type='Polygon',
        #                       geom_coords=None)
        #
        # new_dset = new_dataset(feature,
        #                        source='derived',
        #                        display_name=display_name,
        #                        description=description)
        #
        # prj = os.path.dirname(active_db())
        # dst = os.path.join(prj, cname, new_dset)
        # util.mkdir_if_doesnt_exist(dst)
        # watershed_tif = os.path.join(dst, new_dset + '.tif')
        # boundary_polygon = os.path.join(dst, new_dset + '.shp')
        #
        # # Write a new Shapefile
        # with fiona.open(boundary_polygon, 'w', 'ESRI Shapefile', schema, crs=crs) as c:
        #     for index, boundary in enumerate(boundary_list):
        #         c.write({
        #             'geometry': boundary,
        #             'properties': {'id': index + 1},
        #         })
        #
        # data = watershed.data.astype(out_meta['dtype'])
        # data = np.transpose(data)
        #
        # # rotate image 90 degrees
        # data = np.rot90(data)
        #
        # # write out tif file
        # with rasterio.open(watershed_tif, 'w', **out_meta) as dest:
        #     try:
        #         dest.write(data.astype(out_meta['dtype']))
        #     except ValueError:
        #         dest.write(data.astype(out_meta['dtype']), 1)
        #
        # self.file_path = watershed_tif
        #
        # new_metadata = {
        #     'parameter': orig_metadata['parameter'],
        #     'datatype': orig_metadata['datatype'],
        #     'file_format': orig_metadata['file_format'],
        # }
        #
        # if description is None:
        #     description = 'Raster Filter Applied'
        #
        # # update metadata
        # new_metadata.update({
        #     'options': self.options,
        #     'file_path': self.file_path,
        # })
        # update_metadata(new_dset, quest_metadata=new_metadata, metadata=metadata)
        #
        #
        #
        # return {'datasets': new_dset, 'features': feature}
        #

    def apply_filter_options(self, fmt, **kwargs):
        raise NotImplementedError