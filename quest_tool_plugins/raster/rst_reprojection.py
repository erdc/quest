from quest.plugins import ToolBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db
import os
import rasterio
import subprocess

import param


class RstReprojection(ToolBase):
    _name = 'raster-reprojection'
    operates_on_datatype = ['raster', 'discrete-raster']

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to run tool on.""",
                                         filters={'datatype': 'raster'},
                                         )
    new_crs = param.String(default=None,
                           doc="""New coordinate reference system to project to""")

    def _run_tool(self):

        dataset = self.dataset

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different providers

        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']


        if self.new_crs is None:
            raise ValueError("A new coordinated reference system MUST be provided")

        dst_crs = self.new_crs

        # # save the resulting raster
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
        dst = os.path.join(prj,  cname, new_dset)
        os.makedirs(dst, exist_ok=True)
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
            'options': self.set_options,
            'file_path': self.file_path,
        })
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset, 'features': feature}
