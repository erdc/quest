"""Functions required run raster filters"""
from quest.plugins import FilterBase
from quest import util

from quest.api import get_metadata, new_dataset, update_metadata, new_feature
from quest.api.projects import active_db

import os
import rasterio


class RstBase(FilterBase):
    # metadata attributes
    group = 'raster'
    operates_on_datatype = ['raster']
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = ['raster']
    produces_geotype = None
    produces_parameters = None

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': 'raster'},
                                         )

    def _run_tool(self):

        dataset = self.dataset

        # get metadata, path etc from first dataset, i.e. assume all datasets
        # are in same folder. This will break if you try and combine datasets
        # from different service

        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']

        #run filter
        with rasterio.open(src_path) as src:
            out_image = self._apply(src, orig_metadata)
            out_meta = src.profile
        # save the resulting raster
        out_meta.update({"dtype": out_image.dtype,
                        "height": out_image.shape[0],
                         "width": out_image.shape[1],
                         "transform": None})

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
        dst = os.path.join(dst, new_dset+'.tif')

        with rasterio.open(dst, "w", **out_meta) as dest:
            dest.write(out_image)

        self.file_path = dst

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'unit': orig_metadata['unit']
        }

        # update metadata
        new_metadata.update({
            'options': self.options,
            'file_path': self.file_path,
        })
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset, 'features': feature}

    def _apply(self, df, orig_metadata):
        raise NotImplementedError
