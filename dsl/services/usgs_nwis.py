"""QUEST wrapper for USGS NWIS Services."""

from .base import WebServiceBase
import concurrent.futures
from functools import partial
from builtins import range
import pandas as pd
import os
from ulmo.usgs import nwis
from .. import util, get_pkg_data_path
from builtins import range

BASE_PATH = 'usgs-nwis'


class NwisService(WebServiceBase):
    def _register(self):
        self.metadata = {
            'display_name': 'USGS NWIS Web Services',
            'description': ('Services available through the USGS National '
                            'Water Information System'),
            'organization': {
                'abbr': 'USGS',
                'name': 'United States Geological Survey',
            },
        }

    def _get_services(self):
        return {
            'iv': {
                'display_name': 'NWIS Instantaneous Values Service',
                'description': ('Retrieve current streamflow and other '
                                'real-time data for USGS water sites '
                                'since October 1, 2007'),
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('iv').values()),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Alaska', 'USA', 'Hawaii'],
                'bounding_boxes': [
                    (-178.19453125, 51.6036621094, -130.0140625, 71.4076660156),
                    (-124.709960938, 24.5423339844, -66.9870117187, 49.3696777344),
                    (-160.243457031, 18.9639160156, -154.804199219, 22.2231445312),
                ],
            },
            'dv': {
                'display_name': 'NWIS Daily Values Service',
                'description': ('Retrieve historical summarized daily data '
                                'about streams, lakes and wells. Daily data '
                                'available for USGS water sites include mean, '
                                'median, maximum, minimum, and/or other '
                                'derived values.'),
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('dv').values()),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Alaska', 'USA', 'Hawaii'],
                'bounding_boxes': [
                    (-178.19453125, 51.6036621094, -130.0140625, 71.4076660156),
                    (-124.709960938, 24.5423339844, -66.9870117187, 49.3696777344),
                    (-160.243457031, 18.9639160156, -154.804199219, 22.2231445312),
                ],
            }
        }

    def _get_features(self, service):
        func = partial(_nwis_features, service=service)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            sites = executor.map(func, _states())

        sites = {k: v for d in sites for k, v in d.items()}
        df = pd.DataFrame.from_dict(sites, orient='index')
        # df['_geom_type'] = 'Point'
        for col in ['latitude', 'longitude']:
            df[col] = df['location'].apply(lambda x: float(x[col]))

        df.rename(columns={
                    'code': 'service_id',
                    'name': 'display_name',

                    }, inplace=True)

        # df['_geom_coords'] = list(zip(df['_longitude'], df['_latitude']))
        return df

    def _get_parameters(self, service, features=None):
        if features is None:
            df = self.get_features(service)
        else:
            df = features

        chunks = list(_chunks(df.index.tolist()))
        func = partial(_site_info, service=service)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            data = executor.map(func, chunks)

        data = pd.concat(data, ignore_index=True)

        data['parameter_code'] = data['parm_cd']
        idx = pd.notnull(data['stat_cd'])
        data.loc[idx, 'parameter_code'] += ':' + data['stat_cd']
        data['external_vocabulary'] = 'USGS-NWIS'
        data.rename(columns={
                        'site_no': 'service_id',
                        'count_nu': 'count'
                        },
                    inplace=True)
        data = data[pd.notnull(data['parameter_code'])]
        data['parameter'] = data['parameter_code'].apply(
            lambda x: self._parameter_map(service).get(x)
            )
        pm_codes = _pm_codes()
        data['description'] = data['parm_cd'].apply(
            lambda x: pm_codes.ix[x]['SRSName'] if x in pm_codes.index else ''
            )
        data['unit'] = data['parm_cd'].apply(
            lambda x: pm_codes.ix[x]['parm_unit'] if x in pm_codes.index else ''
            )
        cols = ['parameter', 'parameter_code', 'external_vocabulary',
                'service_id', 'description', 'begin_date',
                'end_date', 'count',
                ]
        data = data[cols]

        # datasets need to have required quest metadata and external metadata
        # need to keep track of units/data classification/restrictions
        return data

    def _parameter_map(self, service, invert=False):
        if service == 'iv':
            pmap = {
                '00060': 'streamflow',
                '00065': 'gage_height',
                '00010': 'water_temperature',
            }
        else:
            pmap = {
                '00060:00003': 'streamflow:mean:daily',
                '00010:00001': 'water_temperature:daily:min',
                '00010:00002': 'water_temperature:daily:max',
                '00010:00003': 'water_temperature:daily:mean',
            }

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def _download(self, service, feature, save_path, dataset,
                  parameter, start=None, end=None, period=None):

        if dataset is None:
            dataset = 'station-' + feature

        if not any([start, end, period]):
            period = 'P365D'  # default to past 1yr of data

        pmap = self._parameter_map(service, invert=True)
        parameter_code, statistic_code = (pmap[parameter].split(':') + [None])[:2]

        data = nwis.get_site_data(feature,
                                  parameter_code=parameter_code,
                                  statistic_code=statistic_code,
                                  start=start, end=end, period=period,
                                  service=service)

        # dict contains only one key since only one parameter/statistic was
        # downloaded, this would need to be changed if multiple
        # parameter/stat were downloaded together
        if not data:
            raise ValueError('No Data Available')

        data = list(data.values())[0]

        # convert to dataframe and cleanup bad data
        df = pd.DataFrame(data['values'])
        if df.empty:
            raise ValueError('No Data Available')
        df = df.set_index('datetime')
        df.value = df.value.astype(float)
        if statistic_code in ['00001', '00002', '00003']:
            df.index = pd.to_datetime(df.index).to_period('D')
        else:
            df.index = pd.to_datetime(df.index)  # this is in UTC

        df[df.values == -999999] = pd.np.nan
        df.rename(columns={'value': parameter}, inplace=True)

        save_path = os.path.join(save_path, BASE_PATH, service)
        save_path = os.path.join(save_path, dataset)
        del data['values']

        metadata = {
            'metadata': data,
            'file_path': save_path,
            'file_format': 'timeseries-hdf5',
            'datatype': 'timeseries',
            'parameter': parameter,
            'unit': data['variable']['units']['code'],
            'service_id': 'svc://usgs-nwis:{}/{}'.format(service, feature)
        }

        # save data to disk
        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        io.write(save_path, df, metadata)
        del metadata['service_id']

        return metadata

    def _download_options(self, service, fmt):
        if fmt == 'smtk':
            parameters = sorted(self._parameter_map(service).values())
            parameters = [(p.capitalize(), p) for p in parameters]
            schema = util.build_smtk('download_options',
                                     'start_end_or_period.sbt',
                                     title='USGS NWIS Download Options',
                                     parameters=parameters)

        if fmt == 'json-schema':
            schema = {
                "title": "USGS NWIS Download Options",
                "type": "object",
                "properties": {
                    "parameter": {
                        "type": "string",
                        "enum": sorted(self._parameter_map(service).values()),
                        "description": "parameter",
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
            }

        return schema


def _chunks(l, n=100):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def _nwis_features(state, service):
    return nwis.get_sites(state_code=state, service=service)


def _nwis_parameters(site, service):
    return {site: list(nwis.get_site_data(site, service=service).keys())}


def _states():
    return [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]


def _parse_rdb(url, index=None):
    df = pd.read_table(url, comment='#')
    if index is not None:
        df.index = df[index]

    df = df.ix[1:] #remove extra header line
    return df


def _pm_codes(update_cache=False):
    url = 'http://help.waterdata.usgs.gov/code/parameter_cd_query?fmt=rdb&group_cd=%'
    cache_file = os.path.join(util.get_cache_dir(), 'usgs_pmcodes.h5')
    if update_cache:
        pm_codes = _parse_rdb(url, index='parm_cd')
    else:
        try:
            pm_codes = pd.read_hdf(cache_file, 'table')
        except:
            pm_codes = _parse_rdb(url, index='parm_cd')
            pm_codes.to_hdf(cache_file, 'table')

    return pm_codes


def _stat_codes():
    url = 'http://help.waterdata.usgs.gov/code/stat_cd_nm_query?stat_nm_cd=%25&fmt=rdb'
    return _parse_rdb(url, index='stat_CD')


def _site_info(sites, service):
    base_url = 'http://waterservices.usgs.gov/nwis/site/?format=rdb,1.0&sites=%s'
    url = base_url % ','.join(sites) + '&seriesCatalogOutput=true&outputDataTypeCd=%s&hasDataTypeCd=%s' % (service, service)
    return _parse_rdb(url)


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
