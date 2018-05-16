from quest.plugins import FilterBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import os
import rasterio
import subprocess
from pyproj import Proj
import param


class RstMerge(FilterBase):
    _name = 'raster-merge'
    group = 'Multi-dataset'
    operates_on_datatype = ['raster','discrete-raster']

    datasets = util.param.DatasetListSelector(default=None,
                                              doc="""Dataset to apply filter to.""",
                                              queries=["datatype == 'raster' or datatype == 'discrete-raster'"],
                                              )
    bbox = param.List(default=None,
                      bounds=(4, 4),
                      class_=float,
                      doc="""bounding box to clip the merged raster to in the form [xmin, ymin, xmax, ymax]""")


    def _apply_filter(self):

        # if len(datasets) < 2:
        #     raise ValueError('There must be at LEAST two datasets for this filter')

        datasets = self.datasets

        orig_metadata = get_metadata(datasets[0])[datasets[0]]
        raster_files = [get_metadata(dataset)[dataset]['file_path'] for dataset in datasets]

        for dataset in datasets:
            if get_metadata(dataset)[dataset]['parameter'] != orig_metadata['parameter']:
                raise ValueError('Parameters must match for all datasets')
            if get_metadata(dataset)[dataset]['unit'] != orig_metadata['unit']:
                raise ValueError('Units must match for all datasets')

        cname = orig_metadata['collection']
        feature = new_feature(cname,
                              # display_name=self.display_name,
                              geom_type='Polygon',
                              geom_coords=None)

        new_dset = new_dataset(feature,
                               source='derived',
                               # display_name=self.display_name,
                               description=self.description)

        self.set_display_name(new_dset)

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

        bbox = self.bbox

        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox
            p = Proj(projection)
            if not p.is_latlong():
                xmin, ymin = p(xmin, ymin)
                xmax, ymax = p(xmax, ymax)
            subprocess.check_output(
                ['gdalwarp', '-overwrite', '-te', str(xmin), str(ymin), str(xmax), str(ymax), output_vrt, dst])
        else:
            subprocess.check_output(
                ['gdal_translate', output_vrt, dst])

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
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset, 'features': feature}
