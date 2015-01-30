from .base import DataServiceBase
import jsonschema
from ulmo.usgs import nwis


class NwisBase(DataServiceBase)
    def register(self):
        self.metadata = {
                    'provider': {
                        'code': 'usgs',
                        'name': 'United States Geological Survey', 
                        },
                    
                    'geographical_areas': ['Alaska', 'USA', 'Hawaii']
                    'bounding_boxes' : [
                            (-178.19453125, 51.6036621094, -130.0140625, 71.4076660156)
                            (-124.709960938, 24.5423339844, -66.9870117187, 49.3696777344)
                            (-160.243457031, 18.9639160156, -154.804199219, 22.2231445312)
                        ],
                    'geotype': 'points',
                    'datatype': 'timeseries',
                }

    def get_locations(self, locations=None, bounding_box=None, parameters=None, service=self.service):
        locations = nwis.get_sites(sites=locations, bounding_box=bounding_box, parameter=parameters, service=service)
        return locations

    def get_location_filters(self): 
        schema = {
            "title": "Location Filters",
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "Optional single or comma delimited list of location identifiers"
                    },
                "bounding_box": {
                    "type": "string",
                    "description": "bounding box should be a comma delimited set of 4 numbers "
                    }
                "parameters": {
                    "type": "string"
                    "description": "comma delimited list of parameter names"
                    }
            }
            "required": None,
        }
        return schema

    def get_data_filters(self):
        schema = {} #todo
        return schema


class UsgsNwisIv(NwisBase):
    def register(self):
        """Register USGS NWIS IV plugin by setting service name, source and uid 
        """
        self.service = 'iv'
        self.metadata.update({
                'display_name': 'NWIS Instantaneous Values',
                'service': 'NWIS Instantaneous Values Web Service', 
                'description': 'For real-time and historical data at USGS water monitoring locations since October 1, 2007,'
            })

    def provides(self, bounding_box=None):
        return ['Streamflow', 'Temperature', 'Precipitation']


class UsgsNwisDv(NwisBase):
    def register(self):
        """Register USGS NWIS DV plugin by setting service name, source and uid 
        """
        self.service = 'dv'
        self.metadata.update({
                'display_name': 'NWIS Daily Values',
                'service': 'NWIS Daily Values Web Service', 
                'description': 'Daily statistical data from the hundreds of thousands of hydrologic sites served by the USGS'
            })

    def provides(self, bounding_box=None):
        return ['Streamflow', 'Temperature', 'Precipitation']
