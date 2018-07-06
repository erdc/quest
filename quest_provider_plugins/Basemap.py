from quest.plugins import ProviderBase, SingleFileServiceBase
from quest.static import ServiceType
from shapely.geometry import box
from itertools import product
from io import BytesIO
from PIL import Image
import pandas as pd
import rasterio
import requests
import param
import math
import os


class BasemapServiceBase(SingleFileServiceBase):
    service_name = "basemap_tile"
    display_name = "Basemap Service"
    description = "Basemap is a tile service."
    service_type = ServiceType.NON_GEO
    datatype = 'image'

    unmapped_parameters_available = True
    _parameter_map = {}

    zoom_level = param.Integer(default=0, doc="", precedence=1)
    lat_1 = param.String(default=0.0, doc="", precedence=2)
    long_1 = param.String(default=0.0, doc="", precedence=3)
    lat_2 = param.String(default=0.0, doc="", precedence=4)
    long_2 = param.String(default=0.0, doc="", precedence=5)
    dst = param.String(default='.', doc="", precedence=6)

    def get_features(self, **kwargs):
        the_feature = {"service_id": "ncep", "display_name": "ncep", "geometry": box(-180, -90, 180, 90)}
        feature = pd.DataFrame(the_feature, index=[0])
        return feature

    def download(self, feature, file_path, dataset, **kwargs):
        p = param.ParamOverrides(self, kwargs)
        url = 'http://c.tile.openstreetmap.org/{0}/{1}/{2}.png'

        combined_latitudes_list = [p.lat_1, p.lat_2]
        convereted_lat_tile_list = [int(1 / (2 * math.pi) * 2 ** p.zoom_level *
                                    (math.pi - math.log(math.tan(math.pi / 4 + math.radians(y) / 2))))
                                    for y in combined_latitudes_list]

        combined_longitudes_list = [p.long_1, p.long_2]
        convereted_long_tile_list = [int(2 ** (p.zoom_level - 1) * (x / 180 + 1)) for x in combined_longitudes_list]

        first_lat = math.degrees(2 * (math.atan(math.exp(math.pi -
                                                         (convereted_long_tile_list[0] * 2 * math.pi)
                                                         / 2 ** p.zoom_level)) - math.pi / 4))

        second_lat = math.degrees(2 * (math.atan(math.exp(math.pi -
                                                          ((convereted_long_tile_list[-1] + 1) * 2 * math.pi)
                                                          / 2 ** p.zoom_level)) - math.pi / 4))

        first_long = math.degrees(convereted_lat_tile_list[0] * 2 * math.pi / (2 ** p.zoom_level) - math.pi)
        second_long = math.degrees((convereted_lat_tile_list[-1] + 1) * 2 * math.pi / (2 ** p.zoom_level) - math.pi)

        number_of_y_tiles = convereted_lat_tile_list[-1] - convereted_lat_tile_list[0]
        if number_of_y_tiles <= 0:
            number_of_y_tiles = 1

        number_of_x_tiles = convereted_long_tile_list[-1] - convereted_long_tile_list[0]
        if number_of_x_tiles <= 0:
            number_of_x_tiles = 1

        lat_range = range(convereted_lat_tile_list[0], (convereted_lat_tile_list[1] + 1))
        long_range = range(convereted_long_tile_list[0], (convereted_long_tile_list[1] + 1))

        loop_iterator = 0
        stitched_image = Image.new('RGB', (number_of_y_tiles * 256, number_of_x_tiles * 256))
        for x, y in product(long_range, lat_range):
            response = requests.get(url.format(p.zoom_level, x, y), verify=False)
            if response.status_code == 200:
                picture_contents = response.content
            if loop_iterator == 0:
                incoming_image = Image.open(BytesIO(picture_contents))
                min_tile_index_width = x
                min_tile_index_height = y
                x = (x - min_tile_index_width) * 256
                y = (y - min_tile_index_height) * 256
                stitched_image.paste(im=incoming_image, box=(x, y))
                incoming_image.close()
                loop_iterator += 1
            else:
                incoming_image = Image.open(BytesIO(picture_contents))
                x = (x - min_tile_index_width) * 256
                y = (y - min_tile_index_height) * 256
                stitched_image.paste(im=incoming_image, box=(x, y))
                incoming_image.close()

        file_path = os.path.join(file_path, dataset + '.png')
        stitched_image.save(file_path)
        src = rasterio.open(file_path, 'r+')
        src.crs = rasterio.crs.CRS.from_epsg(3857)
        src.transform = rasterio.transform.from_bounds(first_long, second_lat, second_long,
                                                       first_lat, number_of_y_tiles * 256, number_of_x_tiles * 256)
        src.close()
        stitched_image.close()


class BasemapProvider(ProviderBase):
    service_list = [BasemapServiceBase]
    publisher_list = None
    display_name = 'Basemap Provider'
    description = 'Services avaliable through the live Basemap Server.'
    organization_name = 'Basemap'
    name = 'Basemap'