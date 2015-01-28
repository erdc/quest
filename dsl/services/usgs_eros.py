"""
Example Services
"""

from dsl.services import base
from ulmo.usgs import eros

class UsgsErosBase(base.DataServiceBase):
    def set_layer(self, product_key, layer_code, layer_name):
        """Register USGS EROS service 
        """

        self.product_key = product_key

        self.metadata = {
                    'provider': {'name': 'USGS', 'id': 'usgs-eros-' + layer_code},
                    'dataset_name': 'USGS Landcover ' + layer_name,
                    'description': 'USGS Landcover ' + layer_name,
                    'geographical area': '???',
                    'bbox': [-180, -90, 180, 90],
                    'geotype': 'polygons',
                    'type': 'raster'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        xmin, ymin, xmax, ymax = bbox

        return eros.get_raster_availability(self.product_key, xmin, ymin, xmax, ymax)


class UsgsErosNlcd2001(UsgsErosBase):
    def register(self):
        self.set_layer('L1L', 'nlcd2006', 'NLCD 2006')
        

class UsgsErosNlcd2006(UsgsErosBase):
    def register(self):
        self.set_layer('L6N', 'nlcd2006', 'NLCD 2006')

