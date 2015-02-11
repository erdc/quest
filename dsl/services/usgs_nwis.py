"""DSL wrapper for USGS NWIS Services

"""
from .base import DataServiceBase
from geojson import Feature, Point, FeatureCollection
import numpy as np
import pandas as pd
import re
import os
from ulmo.usgs import nwis
from .. import util

# default file path (appended to collection path)
DEFAULT_FILE_PATH = 'nwis/'

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

        if locations:
            sites = nwis.get_sites(sites=locations, service=self.service)
            parameters = None
        else:
            if not bounding_box:
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

            parameters = [_as_nwis(p)[0] for p in parameters.split(',')]

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
            properties = {
                            'name': site['name'],
                            'huc': site['huc'],
                            'county': site['county'],
                            'site_type': site['site_type'],
                            'agency': site['agency'],
                            'state_code': site['state_code'],
                        }
            if parameters:
                provides = []
                for parameter in parameters:
                    if site['code'] in site_parameters[parameter]:
                        provides.append(_as_nwis(parameter, invert=True)[0])
                properties.update({'available_parameters': provides})

            feature = Feature(id=site['code'],
                            geometry=Point((float(site['location']['longitude']),
                                            float(site['location']['latitude']))),
                            properties=properties,
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

        if not filter(None, [start, end, period]):
            period = 'P365D' #default to past 1yr of data

        if not parameters:
            parameters = ','.join(self.provides())

        if not path:
            path = util.get_dsl_dir()

        if not isinstance(locations, list):
            locations = [locations]

        path = os.path.join(path, DEFAULT_FILE_PATH)
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver

        parameter_codes = []
        statistic_codes = []
        for parameter in parameters.split(','):
            p, s = _as_nwis(parameter)
            parameter_codes.append(p)
            statistic_codes.append(s)

        parameter_codes = ','.join(set(parameter_codes))
        statistic_codes = filter(None, set(statistic_codes))
        if statistic_codes:
            statistic_codes = ','.join(statistic_codes)
        else:
            statistic_codes=None

        data_locations = {}
        for location in locations:
            datasets = nwis.get_site_data(location, parameter_code=parameter_codes,
                                        statistic_code=statistic_codes,
                                        start=start, end=end, period=period,
                                        service=self.service)

            for code, data in datasets.iteritems():
                df = pd.DataFrame(data['values'])
                if df.empty:
                    print 'No data found, try different time period'
                    continue
                    
                df.index = self._make_index(df)
                df = df['value']
                p, s = _as_nwis(code, invert=True)
                if s:
                    parameter = ':'.join([p,s])
                else:
                    parameter = p

                filename = path + 'nwis:%s_stn:%s_%s.json' % (self.service, location, parameter)
                data_locations[parameter] = filename
                io.write(filename, data['site']['code'], data['site']['name'],
                            data['site']['location']['longitude'], 
                            data['site']['location']['latitude'], 
                            parameter, data['variable']['units']['code'], df)

        return data_locations


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
        return ['streamflow', 'gageheight']

    def _make_index(self, df):
        return pd.to_datetime(df.datetime)


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
        return ['streamflow:dailymean', 
                'gageheight:dailymin', 'gageheight:dailymean', 'gageheight:dailymax']

    def _make_index(self, df):
        return pd.PeriodIndex(df.datetime, freq='D')


def _as_nwis(parameter, invert=False):
    
    if ':' in parameter:
        p, s = parameter.split(':')
    else:
        p, s = parameter, None

    codes = {
            'streamflow': '00060',
            'gageheight': '00065',
        }

    stats = {
        'dailymax': '00001',
        'dailymin': '00002',
        'dailymean': '00003',
        None: None,
    }

    if invert:
        codes = {v: k for k, v in codes.items()}
        stats = {v: k for k, v in stats.items()}
        stats['00011'] = None

    return codes[p], stats[s]
