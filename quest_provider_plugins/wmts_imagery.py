import logging
import math
import os
from io import BytesIO
from itertools import product

import cartopy.crs as ccrs
import numpy as np
import pandas as pd
import param
import requests
import rasterio
from imageio import imread
from quest.static import ServiceType
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from shapely.geometry import box

from quest.plugins import ProviderBase, SingleFileServiceBase
from quest.util import listify

TILE_SIZE = 256
MAX_ZOOM = 19
WMTS_EPSG = 3857

log = logging.getLogger('quest')


class WMTSImageryService(SingleFileServiceBase):
    service_name = "seamless_imagery"
    display_name = "Web Mercator Tile Service"
    description = "Extract seamless imagery from web mapping tile services (WMTS)."
    service_type = ServiceType.GEO_SEAMLESS
    datatype = 'image'

    unmapped_parameters_available = True
    _parameter_map = {}
    url_list = ['http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                'https://s.basemaps.cartocdn.com/light_all/{Z}/{X}/{Y}.png',
                'http://tile.stamen.com/terrain/{Z}/{X}/{Y}.png',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{Z}/{Y}/{X}',
                'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{Z}/{Y}/{X}']

    url = param.ObjectSelector(default=url_list[3], doc="", precedence=1, objects=url_list)
    zoom_level = param.Integer(default=8, bounds=(0, MAX_ZOOM), doc="", precedence=2)
    bbox = param.List(default=[-180, 90, 180, -90], doc="[x-min, y-max, x-max, y-min]", precedence=3)
    crop_to_bbox = param.Boolean(default=True, precedence=4)
    max_tiles = param.Number(
        default=1000,
        bounds=(1, 4**MAX_ZOOM),
        doc="""Maximum number of tiles to allow (a number between 1 and `zoom_level`^4)""",
        precedence=5
    )

    def search_catalog(self, **kwargs):
        catalog_entry_data = {"service_id": "WMTS", "display_name": "WMTS", "geometry": box(-180, -90, 180, 90)}
        catalog = pd.DataFrame(catalog_entry_data, index=[0])
        return catalog

    def download(self, catalog_id, file_path, dataset, **kwargs):
        p = param.ParamOverrides(self, kwargs)
        bbox = listify(p.bbox)

        tile_indices = self._get_indices_from_bbox(*bbox, zoom_level=p.zoom_level)
        pixel_indices = self._get_indices_from_bbox(*bbox, zoom_level=p.zoom_level, as_pixels=True)

        tile_bbox = self._get_bbox_from_indices(*tile_indices, zoom_level=p.zoom_level)
        pixel_bbox = self._get_bbox_from_indices(*pixel_indices, zoom_level=p.zoom_level, from_pixels=True)

        if p.crop_to_bbox:
            upper_left_corner = tile_bbox[0], tile_bbox[3]
            crop_bbox = self._get_crop_bbox(pixel_indices, *upper_left_corner, zoom_level=p.zoom_level)
            adjusted_bbox = pixel_bbox
        else:
            crop_bbox = None
            adjusted_bbox = tile_bbox

        image_array = self._download_and_stitch_tiles(p.url, tile_indices, crop_bbox, p.zoom_level, p.max_tiles)

        file_path = os.path.join(file_path, dataset + '.tiff')

        self._write_image_to_tif(image_array, adjusted_bbox, file_path)

        metadata = {
            'metadata': {'bbox': adjusted_bbox},
            'file_path': file_path,
            'file_format': 'raster-gdal',
            'datatype': 'image',
        }

        return metadata

    @staticmethod
    def _get_indices_from_coordinates(lon, lat, zoom_level, as_pixels=False):
        """Get the x/y indices of the tile or pixel that a lon/lat coordinate falls in at a given zoom level.

        Args:
            lon (float, required):
                longitude coordinate
            lat (float, required):
                latitude coordinate
            zoom_level (int, required):
                 the zoom level of the WMTS tile (or pixel) indices
            as_pixels (bool, optional, default=False:
                If True then return the pixel indices rather than the tile indices

        Returns:
            a tuple of the (x, y) tile/pixel indices
        """
        m = 1
        if as_pixels:
            m = TILE_SIZE
        x = int(m * 2 ** (zoom_level - 1) * (lon / 180 + 1))
        y = int(m / (2 * math.pi) * 2 ** zoom_level *
                (math.pi - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))))

        return x, y

    @staticmethod
    def _get_coordinates_from_indices(x, y, zoom_level, from_pixels=False):
        """Get the lon/lat coordinates of the top-left corner of a tile/pixel given its indices and zoom level.

        Args:
            x (int, required):
                x index of the WMTS tile (or pixel)
            y (int, required):
                y index of the WMTS tile (or pixel)
            zoom_level (int, required):
                the zoom level of the WMTS tile (or pixel) indices
            from_pixels (bool, optional, default=False):
                If True then `x` and `y` are treated as pixel indices rather than tile indices

        Returns:
            (lon, lat) tuple of the top left corner of the pixel or tile.
        """
        m = 1
        if from_pixels:
            m = TILE_SIZE

        lon = math.degrees(
            x * 2 * math.pi / (m * 2**zoom_level) - math.pi
        )

        lat = math.degrees(
            2 * (math.atan(math.exp(math.pi - (y * 2 * math.pi) / (m * 2**zoom_level))) - math.pi / 4)
        )

        return lon, lat

    @classmethod
    def _get_indices_from_bbox(cls, lon_min, lat_min, lon_max, lat_max, zoom_level, as_pixels=False):
        """Get tile/pixel indices that contain a bounding box at the given zoom level.

         Note:
            While the minimum latitude is always on the south (or bottom) side of a bounding box, the minimum
            tile/pixel index is on the north (or top) side.

        Args:
            lon_min (float, required):
                longitude coordinate for the west (left) side of the bbox
            lat_min (float, required):
                latitude coordinate for the south (bottom) side of the bbox
            lon_max (float, required):
                longitude coordinate for the east (right) side of the bbox
            lat_max (float, required):
                latitude coordinate for the north (top) side of the bbox
            zoom_level (int, required):
                the zoom level of the WMTS tile (or pixel) indices
            as_pixels (bool, optional, default=False):
                If True then return the pixel indices rather than the tile indices
        Returns:
            a tuple of tile/pixel indices in the form (xmin, ymin, xmax, ymax).
        """
        xmin, ymin = cls._get_indices_from_coordinates(lon_min, lat_max, zoom_level, as_pixels=as_pixels)
        xmax, ymax = cls._get_indices_from_coordinates(lon_max, lat_min, zoom_level, as_pixels=as_pixels)
        return xmin, ymin, xmax, ymax

    @classmethod
    def _get_bbox_from_indices(cls, xmin, ymin, xmax, ymax, zoom_level, from_pixels=False):
        """Get lon/lat bounding box that completely encompasses a range of tile/pixel indices at a given zoom level.

        Note:
            While the minimum latitude is always on the south (or bottom) side of a bounding box, the minimum
            tile/pixel index is on the north (or top) side.

        Args:
            xmin (int, required):
                x index of the tile/pixel for the north (top) side of the bbox
            ymin (int, required):
                y index of the tile/pixel for the west (left) side of the bbox
            xmax (int, required):
                x index of the tile/pixel for the south (bottom) side of the bbox
            ymax (int, required):
                y index of the tile/pixel for the east (right) side of the bbox
            zoom_level (int, required):
                the zoom level of the WMTS tile (or pixel) indices
            from_pixels (bool, optional, default=False):
                If True then `x` and `y` are treated as pixel indices rather than tile indices

        Returns:
            a tuple of lon/lat coordinates forming a bounding box in the form (lon_min, lat_min, lon_max, lat_max).
        """
        lon_min, lat_max = cls._get_coordinates_from_indices(xmin, ymin, zoom_level, from_pixels=from_pixels)
        # to get the coordinates at the bottom-right corner xmax and ymax are incremented
        lon_max, lat_min = cls._get_coordinates_from_indices(xmax + 1, ymax + 1, zoom_level, from_pixels=from_pixels)
        return lon_min, lat_min, lon_max, lat_max

    @classmethod
    def _get_crop_bbox(cls, pixel_indices, lon_min, lat_max, zoom_level):
        """Get the relative pixel indices of a bounding box given the coordinates of a new origin.

        Note:
            This is used to determine the indices to crop out of an image of stitched tiles.

        Args:
            pixel_indices (tuple, required):
                tuple of pixel indices in the form (xmin, ymin, xmax, ymax)
            lon_min (float, required):
                longitude coordinate of the top-left corner of the stitched tiles
            lat_max (float, required):
                latitude coordinate of the top-left corner of the stitched tiles
            zoom_level (int, required):
                the zoom level of the WMTS tile (or pixel) indices
        Returns:
            a tuple of pixel indices relative the the new origin in the form (xmin, ymin, xmax, ymax).
        """

        # calculate the offset by finding the pixel indices of the top-right corner
        x_pixel_offset, y_pixel_offset = cls._get_indices_from_coordinates(lon_min, lat_max,
                                                                            zoom_level, as_pixels=True)

        # calculate the crop bbox in pixel indices relative to the new image from stitched tiles
        xmin_pixel, xmax_pixel = [index - x_pixel_offset for index in pixel_indices[::2]]
        ymin_pixel, ymax_pixel = [index - y_pixel_offset for index in pixel_indices[1::2]]
        return xmin_pixel, ymin_pixel, xmax_pixel, ymax_pixel

    @staticmethod
    def _download_and_stitch_tiles(url, tile_indices, crop_bbox, zoom_level, max_tiles):
        """Download a set of WMTS tiles and stitch them into a single image.

        Args:
            url (string, required):
                url template for the WMTS service to get tiles from with `{X}` `{Y}`, and `{Z}` placeholders
            tile_indices (tuple, required):
                a tuple of tile indices indicating the range of tiles to download in the form (xmin, ymin, xmax, ymax)
            crop_bbox (tuple, required):
                a tuple of pixel indices relative to the stitched image to crop the image by. If `None` then image
                 won't be cropped.
            zoom_level (int, required):
                the zoom level of the WMTS tile indices
            max_tiles (int, required):
                a number between 1 and `zoom_level`^4 to limit the number of tiles retrieved.

        Raises:
            ValueError: if the number of tiles that would be downloaded exceed `max_tiles`

        Returns:
            A numpy array containing the stitched (and possibly cropped) tiles.
        """
        xmin, ymin, xmax, ymax = tile_indices

        # create ranges to use to iterate over all tile index combinations for downloading
        x_range = range(xmin, xmax + 1)  # add one to the last number in the range because it is non-inclusive
        y_range = range(ymin, ymax + 1)

        number_of_x_tiles = len(x_range)
        number_of_y_tiles = len(y_range)
        total_number_of_tiles = number_of_x_tiles * number_of_y_tiles
        if total_number_of_tiles > max_tiles:
            raise ValueError("{} tiles were requested, which exceeds the maximum tile limit of {}. "
                             "Either increase the tile limit (max_tiles) or decrease the zoom level."
                             .format(total_number_of_tiles, max_tiles))
        else:
            log.info("There are {} tiles to download.".format(total_number_of_tiles))

        # calculate full image height and width (count is calculated on the first time in the loop)
        height = number_of_y_tiles * TILE_SIZE
        width = number_of_x_tiles * TILE_SIZE
        full_image = None

        for x, y in product(x_range, y_range):
            internet_status = requests.Session()
            retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            if 'https' in url:
                internet_status.mount('https://', HTTPAdapter(max_retries=retries))
            elif 'http' in url:
                internet_status.mount('http://', HTTPAdapter(max_retries=retries))
            output_feedback = internet_status.get(url.format(Z=zoom_level, X=x, Y=y), verify=True)
            if output_feedback.status_code == 200:
                image = imread(BytesIO(output_feedback.content))
                image = np.moveaxis(image, -1, 0)  # move the bands from the last axis to the first.

                x_pixel_min, x_pixel_max = (x - xmin) * TILE_SIZE, (x - xmin + 1) * TILE_SIZE
                y_pixel_min, y_pixel_max = (y - ymin) * TILE_SIZE, (y - ymin + 1) * TILE_SIZE

                # initialize full image on first loop
                if full_image is None:
                    count, _, _ = image.shape
                    full_image = np.empty([count, height, width], dtype=np.uint8)

                full_image[:, y_pixel_min:y_pixel_max, x_pixel_min:x_pixel_max] = image

        if crop_bbox:
            xmin, ymin, xmax, ymax = crop_bbox
            cropped_image = full_image[:, ymin:ymax, xmin:xmax]

        return cropped_image

    @staticmethod
    def _write_image_to_tif(array, bbox, file_path):
        """Write an RGB array as a GeoTiff with a WebMercator CRS.

        Args:
            array (numpy array, required):
                three band array of RGB values of an image
            bbox (tuple, required):
                lon/lat bounding box for image in the form (lon_min, lat_min, lon_max, lat_max)
            file_path (string, required):
                file path to save the GeoTiff to
        """
        bbox = np.array(bbox).reshape(2, 2)
        bbox = ccrs.GOOGLE_MERCATOR.transform_points(ccrs.PlateCarree(), bbox[:, 0], bbox[:, 1]).reshape(6)
        bbox = bbox[0], bbox[1], bbox[3], bbox[4]
        count, height, width = array.shape
        indexes = list(range(1, count + 1))
        transform = rasterio.transform.from_bounds(*bbox, width=width, height=height)
        crs = rasterio.crs.CRS.from_epsg(WMTS_EPSG)
        with rasterio.open(file_path, 'w', driver='GTiff', height=height,
                           width=width, count=count, dtype=array.dtype,
                           crs=crs, transform=transform) as dst:
            dst.write(array, indexes=indexes)


class WMTSImageryProvider(ProviderBase):
    service_list = [WMTSImageryService]
    publisher_list = None
    display_name = 'WMTS Imagery Provider'
    description = 'Extract seamless imagery from web mapping tile services (WMTS).'
    organization_name = 'N/A'
    name = 'wmts'
