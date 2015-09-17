"""DSL wrapper for USGS NWIS Services

"""
from __future__ import division
from __future__ import print_function
from builtins import str
from past.utils import old_div
from .base import DataServiceBase
from geojson import Feature, Point, FeatureCollection
import numpy as np
import pandas as pd
import re
import os
from ulmo.usgs import nwis
from .. import util

# default file path (appended to collection path)
DEFAULT_FILE_PATH = os.path.join('usgs','nwis')

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
            sites = nwis.get_sites(sites=util.stringify(locations), service=self.service)
            parameters = None
        else:
            if bounding_box is None:
                bounding_box = [-124.7099609, 24.54233398, -66.98701171, 49.36967773]

            xmin, ymin, xmax, ymax = [float(x) for x in bounding_box]
            
            #limit boxes < 5x5 decimal degree size
            boxes = []
            x = np.linspace(xmin, xmax, np.ceil(old_div((xmax-xmin),5.0))+1)
            y = np.linspace(ymin, ymax, np.ceil(old_div((ymax-ymin),5.0))+1)
            for i, xd in enumerate(x[:-1]):
                x1, x2 = x[i], x[i+1]
                for j, yd in enumerate(y[:-1]):            
                    y1, y2 = y[j], y[j+1]
                    boxes.append(','.join([str(round(n,7)) for n in [x1,y1,x2,y2]]))

            if parameters is None:
                parameters = self.provides()

            parameters = [_as_nwis(p)[0] for p in parameters]

            sites = {}
            site_parameters = {}
            for parameter in parameters:
                site_parameters[parameter] = []
                for box in boxes:
                    sites_in_box = nwis.get_sites(sites=util.stringify(locations), bounding_box=box, 
                            parameter_code=parameter, service=self.service)
                    sites.update(sites_in_box)
                    site_parameters[parameter].extend([site['code'] for site in list(sites_in_box.values())])
                    
        features = []
        for site in list(sites.values()):
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

    def get_locations_options(self): 
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

    def get_data_options(self, **kwargs):
        schema = {
            "title": "USGS NWIS Download Options",
            "type": "object",
            "properties": {
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
        }
        return schema

    def get_data(self, locations, parameters=None, path=None, start=None, end=None, period=None):
        
        if not any([start, end, period]):
            period = 'P365D' #default to past 1yr of data

        if parameters is None:
            parameters = self.provides()

        if path is None:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH)
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver

        parameter_codes = []
        statistic_codes = []
        for parameter in parameters:
            p, s = _as_nwis(parameter)
            parameter_codes.append(p)
            statistic_codes.append(s)

        parameter_codes = ','.join(set(parameter_codes))
        statistic_codes = [_f for _f in set(statistic_codes) if _f]
        if statistic_codes:
            statistic_codes = ','.join(statistic_codes)
        else:
            statistic_codes=None

        data_files = {}
        for location in locations:
            data_files[location] = {}
            datasets = nwis.get_site_data(location, parameter_code=parameter_codes,
                                        statistic_code=statistic_codes,
                                        start=start, end=end, period=period,
                                        service=self.service)

            for code, data in datasets.items():
                df = pd.DataFrame(data['values'])
                if df.empty:
                    print('No data found, try different time period')
                    continue
                    
                df.index = self._make_index(df)
                p, s = _as_nwis(code, invert=True)
                if s:
                    parameter = ':'.join([p,s])
                else:
                    parameter = p

                df = df[['value']]
                df.value = df.value.apply(np.float)
                df.columns = [parameter + '(%s)' % data['variable']['units']['code']]
                filename = path + 'nwis_%s_stn_%s_%s.json' % (self.service, location, parameter)
                data_files[location][parameter] = filename
                location_id = data['site']['code']
                geometry = Point((float(data['site']['location']['longitude']), float(data['site']['location']['latitude'])))
                metadata = data['site']
                io.write(filename, location_id=location_id, geometry=geometry, dataframe=df, metadata=metadata)

        return data_files


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
        return ['streamflow:dailymin','streamflow:dailymean','streamflow:dailymax', 
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
        codes = {v: k for k, v in list(codes.items())}
        stats = {v: k for k, v in list(stats.items())}
        stats['00011'] = None

    return codes[p], stats[s]
