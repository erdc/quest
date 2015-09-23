"""DSL wrapper for USGS NWIS Services

"""
from .base import DataServiceBase
from multiprocessing import Pool
import pandas as pd
import re
import os
from ulmo.usgs import nwis
from .. import util


states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

def _nwis_iv_features(state):
    return nwis.get_sites(state_code=state, service='iv')

def _nwis_iv_parameters(site):
    return {site: nwis.get_site_data(site, service='iv').keys()}

def _pm_codes():
    url = (
        'http://nwis.waterdata.usgs.gov/usa/nwis/pmcodes'
        '?radio_pm_search=param_group&pm_group=All+--+include+all+parameter+groups'
        '&pm_search=&casrn_search=&srsname_search=&format=rdb_file'
        '&show=parameter_group_nm&show=parameter_nm&show=casrn&show=srsname&show=parameter_units'
    )

    df = pd.read_table(url, comment='#')
    df.index = df[df.columns[0]]
    df = df.ix[1:] #remove extra header line
    return df

def _stat_codes():
    url = 'http://help.waterdata.usgs.gov/code/stat_cd_nm_query?stat_nm_cd=%25&fmt=rdb'
    df = pd.read_table(url, comment='#')
    df.index = df[df.columns[0]]
    df = df.ix[1:] #remove extra header line
    return df

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

    def get_features(self, processes=20):
        p = Pool(processes)
        sites = p.map(_nwis_iv_features, states)
        p.close()
        p.terminate()
        sites = {k: v for d in sites for k, v in d.items()}
        df = pd.DataFrame.from_dict(sites, orient='index')
        for col in ['latitude', 'longitude', 'srs']:
            df[col] = df['location'].apply(lambda x: x[col])

        return df

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

    def download_dataset_options(self, **kwargs):
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

    def download_data(self, feature, parameter, path, start=None, end=None, period=None):
        
        if not any([start, end, period]):
            period = 'P365D' #default to past 1yr of data

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
