from quest.plugins import ProviderBase, SingleFileServiceBase
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from quest.static import ServiceType
from shapely.geometry import box
from itertools import product
from io import BytesIO
from PIL import Image
import pandas as pd
import numpy as np
import requests
import rasterio
import param
import math
import os


class BasemapServiceBase(SingleFileServiceBase):
    service_name = "Web Mercator Tile Service"
    display_name = "WMTS"
    description = "WMTS gives tiles of different layers."
    service_type = ServiceType.NON_GEO
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

    url = param.ObjectSelector(default=None, doc="", precedence=1, objects=url_list)
    zoom_level = param.Integer(default=0, doc="", precedence=2)
    bbox = param.String(default="-180, 90, 180, -90", doc="x-min, y-max, x-max, y-min", precedence=3)

    def get_features(self, **kwargs):
        the_feature = {"service_id": "WMTS", "display_name": "WMTS", "geometry": box(-180, -90, 180, 90)}
        feature = pd.DataFrame(the_feature, index=[0])
        return feature

    def download(self, feature, file_path, dataset, **kwargs):
        p = param.ParamOverrides(self, kwargs)
        if not isinstance(p.bbox, (list,)):
            if ", " in p.bbox:
                bbox = p.bbox.split(", ")
                bbox = [float(x) for x in bbox]
            else:
                print("There was an issue with the format of your boudning box.")
        else:
            bbox = p.bbox

        # Get the basemap tiles for the given coordinates.
        converted_lat_tile_list = [int(1 / (2 * math.pi) * 2 ** p.zoom_level *
                                   (math.pi - math.log(math.tan(math.pi / 4 + math.radians(y) / 2))))
                                   for y in [bbox[3], bbox[1]]]
        converted_long_tile_list = [int(2 ** (p.zoom_level - 1) * (x / 180 + 1)) for x in [bbox[0], bbox[2]]]
        converted_lat_tile_list.sort()
        converted_long_tile_list.sort()

        # Get the top left and bottom right hand corner coordinates of where the actual basemap tile starts.
        # The top left hand corner of the bbox will not have the coordinates as the basemap tile because of
        # - them never going to line up perfectly.
        # We have to increment the long and lat of the bottom right hand corner because we need to get the next
        # - tile and caculate the coordinates of its top left hand corner.
        # Why I am doing this is because we have to geo-reference the image and have the exact coordinates of the
        # - actual image that we will stitch together from these tiles.
        first_lat = math.degrees(
            2 * (math.atan(math.exp(math.pi - (converted_long_tile_list[0] * 2 * math.pi) / 2**p.zoom_level)) -
                 math.pi / 4)
        )
        second_lat = math.degrees(
            2 * (math.atan(math.exp(math.pi - ((converted_long_tile_list[-1] + 1) * 2 * math.pi) / 2**p.zoom_level)) -
                 math.pi / 4)
        )

        first_long = math.degrees(
            converted_lat_tile_list[0] * 2 * math.pi / (2**p.zoom_level) - math.pi
        )
        second_long = math.degrees(
            (converted_lat_tile_list[-1] + 1) * 2 * math.pi / (2**p.zoom_level) - math.pi
        )

        # Have to create a range item so that we can do a product on it later in the algorithm. So lets increment,
        # - the last element in either list to include up to the next number. If we didn't then it would stop short
        # - one number.
        # Next I have to figure out the number of tiles for x and y, so that I can see how big the image is going
        # - to be.
        # We have to increment the last elemeent in the list because Python range function is not inclusive of the last
        # - number.
        lat_range_list = range(converted_lat_tile_list[0], (converted_lat_tile_list[1] + 1))
        number_of_y_tiles = len(lat_range_list)

        long_range_list = range(converted_long_tile_list[0], (converted_long_tile_list[1] + 1))
        number_of_x_tiles = len(long_range_list)

        if (number_of_x_tiles * number_of_y_tiles) > 1000:
            raise ValueError("This will take way to long, so exiting...")

        # This loop will create the image from the previous calculated size, by multiplying the number of tiles for
        # - x and y by 256 (pixels). This is the standard size for every tile (256,256) for open street map. Next,
        # - I will do the product on the range of both the lat and long. This will give me all the tiles from the
        # - top left corner to the the bottom right. Then, I have a dictionary that sets the z, x, and y to the upper
        # - and lower value. I do this because there will be an Z, X, and Y at the end of the URL that I will want to
        # - inject the values into, and won't know if the incoming x, y, z will be capitialized or lowercase. Next, I
        # - format the url with the given zoom_level, and calculated tile number to download. Next, I setup a request
        # - session to make sure that I can have retries to download a tile if one fails. Then, If I get a good
        # - response then I check to see if we are on the first iteration, to set my min x and y tile numbers. I do
        # - this because I need the baseline to subtract all future tile numbers from in order to acurately know where
        # - each tile will go in the  grid. This has to be done this way because not all tiles will be retrieved in
        # - order, and this saves lines of code by not having to make sure that the pictures are all in order. Next,
        # - I increment my iterator so I don't come back into the if statment, I open the image in memory, then
        # - subtract the baseline x and y from the current  tile number, and multiply by the number of pixels.
        # - Ex: (4 - 2) * 256 = 512 for x. This will put the picture right at the calculated number of pixels either
        # - over or down. Next I stitch the opened image to the one I created at the beinging of the loop. This will
        # - hold all the images once they are all stitched in. Lastly, I close the image that is opened in memory.
        loop_iterator = 0
        stitched_image = Image.new('RGB', (number_of_x_tiles * 256, number_of_y_tiles * 256))
        for x, y in product(long_range_list, lat_range_list):
            # key = {"Z": p.zoom_level, "z": p.zoom_level, "X": x, "x": x, "Y": y, "y": y}
            internet_status = requests.Session()
            retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            if 'https' in p.url:
                internet_status.mount('https://', HTTPAdapter(max_retries=retries))
            elif 'http' in p.url:
                internet_status.mount('http://', HTTPAdapter(max_retries=retries))
            output_feedback = internet_status.get(p.url.format(Z=p.zoom_level, X=x, Y=y), verify=True)
            if output_feedback.status_code == 200:
                if loop_iterator == 0:
                    min_tile_index_width = x
                    min_tile_index_height = y

                incoming_image = Image.open(BytesIO(output_feedback.content))
                x = (x - min_tile_index_width) * 256
                y = (y - min_tile_index_height) * 256
                stitched_image.paste(im=incoming_image, box=(x, y))
                incoming_image.close()
                loop_iterator += 1

        # Here I will output the image to the desktop and not the browser. This is because the image can be several
        # - 100 megabytes big, depending on the given zoom level. Next, I save the image to the current working
        # - directory. Next, I load the image from memory into a numpy array, and close the image. I do this here
        # - becasue if the image is big then we can free up all of our memory for the numpy array. Next, I take the
        # - transform for our geo-referenced image. The transform operation will take the calcuated coordinates of
        # - out top left and bottom right tiles, and the width and height of the image. Next, I have to move the axis
        # - around so that our number of bands is in front of the tuple, rather than at the back. Since our image is
        # - RGB, the number of bands is 3, for three colors. Next, I take the image that is in the numpy array and
        # - open it with the rasterio call. Lastly, I write the image to disk, and print out where the file was saved
        # - to and the size of the image.
        file_path = os.path.join(file_path, dataset + '.tiff')
        image_array = np.array(stitched_image)
        stitched_image.close()
        transform = rasterio.transform.from_bounds(first_long, second_lat, second_long,
                                                   first_lat, number_of_x_tiles * 256, number_of_y_tiles * 256)
        image_array = np.moveaxis(image_array, -1, 0)
        with rasterio.open(file_path, 'w', driver='GTiff', height=image_array.shape[1],
                           width=image_array.shape[2], count=image_array.shape[0], dtype=image_array.dtype,
                           crs='EPSG:3957', transform=transform) as dst:
            dst.write(image_array, indexes=[1, 2, 3])
        metadata = {
            'metadata': 'Image Downloaded',
            'file_path': file_path,
            'file_format': 'geo-tiff',
            'datatype': 'image',
            'parameter': "unkown",
            'unit': "unkown",
        }

        return metadata


class BasemapProvider(ProviderBase):
    service_list = [BasemapServiceBase]
    publisher_list = None
    display_name = 'Basemap Provider'
    description = 'Services avaliable through the live Basemap Server.'
    organization_name = 'Basemap'
    name = 'basemap'
