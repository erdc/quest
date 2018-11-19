import param
import rasterio
import rasterio.mask
import rasterio.merge
import geopandas as gpd
from fiona.crs import from_epsg
from shapely.geometry import box

from quest import util
from quest.plugins import ToolBase
from quest.static import DataType, UriType
from quest.api import get_metadata, update_metadata


class RstMerge(ToolBase):
    _name = 'raster-merge'
    group = 'Multi-dataset'
    operates_on_datatype = [DataType.RASTER, 'discrete-raster']

    datasets = util.param.DatasetListSelector(default=None,
                                              doc="""Dataset to run tool on.""",
                                              queries=["datatype == 'raster' or datatype == 'discrete-raster'"],
                                              )
    bbox = param.List(default=None,
                      bounds=(4, 4),
                      class_=float,
                      doc="""bounding box to clip the merged raster to in the form [xmin, ymin, xmax, ymax]""")

    def _run_tool(self):

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

        new_metadata = {
            'parameter': orig_metadata['parameter'],
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'unit': orig_metadata['unit'],
        }

        new_dset, file_path, catalog_entry = self._create_new_dataset(
            old_dataset=datasets[0],
            ext='.tif',
            dataset_metadata=new_metadata,
        )

        open_datasets = [rasterio.open(d) for d in raster_files]
        profile = open_datasets[0].profile
        # hack to avoid nodata out of range of dtype error for NED datasets
        profile['nodata'] = -32768.0 if profile['nodata'] == -3.4028234663853e+38 else profile['nodata']
        new_data, transform = rasterio.merge.merge(open_datasets, nodata=profile['nodata'])
        for d in open_datasets:
            d.close()
        profile.pop('tiled', None)
        profile.update(
            height=new_data.shape[1],
            width=new_data.shape[2],
            transform=transform,
            driver='GTiff'
        )
        with rasterio.open(file_path, 'w', **profile) as output:
            output.write(new_data.astype(profile['dtype']))

        bbox = self.bbox

        if bbox is not None:
            bbox = box(*bbox)
            geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
            geo = geo.to_crs(crs=profile['crs'])
            bbox = geo.geometry

            with rasterio.open(file_path, 'r') as merged:
                new_data, transform = rasterio.mask.mask(dataset=merged, shapes=bbox, all_touched=True, crop=True)

            # profile.pop('tiled', None)
            profile.update(
                height=new_data.shape[1],
                width=new_data.shape[2],
                transform=transform,
            )
            with rasterio.open(file_path, 'w', **profile) as clipped:
                clipped.write(new_data)

        with rasterio.open(file_path) as f:
            geometry = util.bbox2poly(f.bounds.left, f.bounds.bottom, f.bounds.right, f.bounds.top, as_shapely=True)
        update_metadata(catalog_entry, quest_metadata={'geometry': geometry.to_wkt()})

        return {'datasets': new_dset, 'catalog_entries': catalog_entry}
