"""DSL wrapper for USGS NWIS Services

"""
from .base import DataServiceBase
from geojson import Feature, Point, FeatureCollection
import numpy as np
import re
from ulmo.usgs import nwis
from .. import util

# default file path (appended to collection path)
DEFAULT_FILE_PATH = 'nwis'

class NwisBase(DataServiceBase):
    def register(self):
        self.metadata = {
                    'provider': {
                        'abbr': 'USGS',
                        'name': 'United States Geological Survey', 
                        },
                    
                    'geographical_areas': ['Alaska', 'USA', 'Hawaii'],
                    'bounding_boxes' : [
                            (-178.19453125, 51.6036621094, -130.0140625, 71.4076660156),
                            (-124.709960938, 24.5423339844, -66.9870117187, 49.3696777344),
                            (-160.243457031, 18.9639160156, -154.804199219, 22.2231445312),
                        ],
                    'geotype': 'points',
                    'datatype': 'timeseries',
                }

    def get_locations(self, locations=None, bounding_box=None, parameters=None):
        if not locations and not bounding_box:
            bounding_box = '-124.7099609, 24.54233398, -66.98701171, 49.36967773'

        #clean up bounding box
        xmin, ymin, xmax, ymax = [float(x) for x in bounding_box.split(',')]

        #limit boxes < 5x5 decimal degree size
        boxes = []
        x = np.linspace(xmin, xmax, np.ceil((xmax-xmin)/5.0)+1)
        y = np.linspace(ymin, ymax, np.ceil((ymax-ymin)/5.0)+1)
        for i, xd in enumerate(x[:-1]):
            x1, x2 = x[i], x[i+1]
            for j, yd in enumerate(y[:-1]):            
                y1, y2 = y[j], y[j+1]
                boxes.append(','.join([str(round(n,7)) for n in [x1,y1,x2,y2]]))

        if not parameters:
            parameters = ','.join(self.provides())

        parameters = _as_nwis(parameters)
        parameters = parameters.split(',')

        sites = {}
        site_parameters = {}
        for parameter in parameters:
            site_parameters[parameter] = []
            for box in boxes:
                sites_in_box = nwis.get_sites(sites=locations, bounding_box=box, 
                        parameter_code=parameter, service=self.service)
                sites.update(sites_in_box)
                site_parameters[parameter].extend([site['code'] for site in sites_in_box.values()])
                
        features = []
        for site in sites.values():
            provides = []
            for parameter in parameters:
                if site['code'] in site_parameters[parameter]:
                    provides.append(_as_nwis(parameter, invert=True))

            feature = Feature(id=site['code'],
                            geometry=Point((float(site['location']['longitude']),
                                            float(site['location']['latitude']))),
                            properties={
                                'name': site['name'],
                                'huc': site['huc'],
                                'county': site['county'],
                                'site_type': site['site_type'],
                                'agency': site['agency'],
                                'state_code': site['state_code'],
                                'available_parameters': provides,
                            },
                        )
            features.append(feature)

        return FeatureCollection(features)

    def get_location_filters(self): 
        schema = {
            "title": "Location Filters",
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "Optional single or comma delimited list of location identifiers",
                    },
                "bounding_box": {
                    "type": "string",
                    "description": "bounding box should be a comma delimited set of 4 numbers ",
                    },
                "parameters": {
                    "type": "string",
                    "description": "comma delimited list of parameter names",
                    },
                "all_parameters_required": {
                    "type": "boolean",
                    "description": "If true only locations where all parameters exist will be shown"
                }
            },
            "required": None,
        }
        return schema

    def get_data_filters(self):
        schema = {
            "title": "Download Options",
            "type": "Object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "single or comma delimited list of location identifiers to download data for",
                },
                "parameters": {
                    "type": "string",
                    "description": "single or comma delimited list of parameters to download data for"

                },
                "start": {
                    "type": "string",
                    "description": "start date",
                },
                "end": {
                    "type": "string",
                    "description": "end date",
                },
                "period": {
                    "type": "string",
                    "description": "period date",
                },
            },
            "required": ["locations", "parameters"],
        }
        return schema

    def get_data(self, locations, parameters=None, path=None, start=None, end=None, period=None):
        if not parameters:
            parameters = self.provides()

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH)
        io = util.load_drivers('io', 'ts-geojson')

        parameters = _as_nwis(parameters)
        for location in locations:
            datasets = nwis.get_site_data(location, parameter_code=parameters, 
                                      start=start, end=end, period=period,
                                      service=self.service)

            for parameter, data in datasets.iteritems():
                parameter = _as_nwis(parameter.split(':')[0], invert=True)
                filename = path + '_%s_%s.json' % (location, parameter, self.service)
                io.write(path, )



class NwisIv(NwisBase):
    def register(self):
        """Register USGS NWIS IV plugin by setting service name, source and uid 
        """
        super(NwisIv, self).register()
        self.service = 'iv'
        self.metadata.update({
                'display_name': 'NWIS Instantaneous Values',
                'service': 'NWIS Instantaneous Values Web Service', 
                'description': 'For real-time and historical data at USGS water monitoring locations since October 1, 2007,'
            })

    def provides(self, bounding_box=None):
        return ['Streamflow', 'Gage Height']


class NwisDv(NwisBase):
    def register(self):
        """Register USGS NWIS DV plugin by setting service name, source and uid 
        """
        super(NwisDv, self).register()
        self.service = 'dv'
        self.metadata.update({
                'display_name': 'NWIS Daily Values',
                'service': 'NWIS Daily Values Web Service', 
                'description': 'Daily statistical data from the hundreds of thousands of hydrologic sites served by the USGS'
            })

    def provides(self, bounding_box=None):
        return ['Streamflow', 'Gage Height']


def _as_nwis(parameters, invert=False):
    if not parameters:
        return None

    nwis = {
        'Streamflow': '00060',
        'Gage Height': '00065',
    }
    if invert:
        nwis = {v: k for k, v in nwis.items()}

    return ','.join([nwis[parameter.strip()] for parameter in parameters.split(',')])
