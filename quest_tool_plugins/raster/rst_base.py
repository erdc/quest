import rasterio

from quest import util
from quest.plugins import ToolBase
from quest.api import get_metadata
from quest.static import DataType, UriType


class RstBase(ToolBase):
    # metadata attributes
    group = 'raster'
    operates_on_datatype = [DataType.RASTER]
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = [DataType.RASTER]
    produces_geotype = None
    produces_parameters = None

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': DataType.RASTER},
                                         )

    def _run_tool(self):

        dataset = self.dataset
        orig_metadata = get_metadata(dataset)[dataset]
        src_path = orig_metadata['file_path']

        #run filter
        with rasterio.open(src_path) as src:
            out_image = self._run(src, orig_metadata)
            out_meta = src.profile
        # save the resulting raster
        out_meta.update({"dtype": out_image.dtype,
                        "height": out_image.shape[0],
                         "width": out_image.shape[1],
                         "transform": None})

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'unit': orig_metadata['unit']
        }

        new_dset, file_path, catalog_entry = self._create_new_dataset(
            old_dataset=dataset,
            ext='.tif',
            dataset_metadata=new_metadata,
        )

        with rasterio.open(file_path, "w", **out_meta) as dest:
            dest.write(out_image)

        return {'datasets': new_dset, 'catalog_entries': catalog_entry}

    def _run(self, df, orig_metadata):
        raise NotImplementedError
