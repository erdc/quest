"""DSL wrapper for NCDC GHCN and GSOD Services."""
from .base import WebServiceBase
from .. import util
import pandas as pd
import os

BASE_PATH = 'noaa'
BASE_URL = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/'

# noaa_url = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/nosCoopsCA.csvp?stationID%2CstationName%2CdateEstablished%2Clongitude%2Clatitude'

class NoaaService(WebServiceBase):
    def _register(self):
        self.metadata = {
            'display_name': 'NOAA Coastwatch ERDDAP Web Services',
            'description': 'Services available from NOAA' ,
            'organization': {
                'abbr': 'NOAA',
                'name': 'National Oceanic and Atmospheric Administration',
            },
        }

    def _get_services(self):
        return {
            'ndbc': {
                'display_name': 'NOAA National Data Buoy Center',
                'description': 'NDBC Standard Meteorological Buoy Data',
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('ndbc').values()),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes': [
                    [-177.75, -27.705, 179.001, 71.758],
                ],
            },
            'coops': {
                'display_name': 'NOAA COOPS',
                'description': 'Center for Operational Oceanographic Products '
                               'and Services',
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('coops').values()),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes': [
                    [-180, -90, 180, 90],
                ],
            },
        }

    def _get_features(self, service):
        if service == 'ndbc':
            ndbc_url = BASE_URL + 'cwwcNDBCMet.csvp?station%2Clongitude%2Clatitude'
            df = pd.read_csv(ndbc_url)
            df.rename(columns={
                'station': '_service_id',
                'longitude (degrees_east)': '_longitude',
                'latitude (degrees_north)': '_latitude'
                }, inplace=True)

            df['_display_name'] = df['_service_id']
            df['_geom_type'] = 'Point'
            df['_geom_coords'] = zip(df['_longitude'], df['_latitude'])

        if service == 'coops':
            raise NotImplementedError

        return df

    def _get_parameters(self, service, features=None):
        # hardcoding for now
        if service == 'ndbc':
            parameters = {
                '_parameters': list(self._parameter_map('ndbc').values()),
                '_parameter_codes': list(self._parameter_map('ndbc').keys())
            }

        if service == 'coops':
            parameters = {
                '_parameters': list(self._parameter_map('coops').values()),
                '_parameter_codes': list(self._parameter_map('coops').keys())
            }

        return parameters

    def _parameter_map(self, service, invert=False):
        if service == 'ndbc':
            pmap = {
                'wd': 'wind_direction',
                'wspd': 'wind_from_direction',
                'gst': 'wind_speed_of_gust',
                'wvht': 'wave_height',
                'wtmp': 'sea_surface_temperature',
                'atmp': 'air_temperature',
                'bar': 'air_pressure',
                'tide': 'water_level',
                'wspu': 'eastward_wind',
                'wspv': 'northward_wind',
            }

        if service == 'coops':
            pmap = {
            }

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def _download(self, service, feature, save_path, dataset,
                  parameter, start=None, end=None):

        if end is None:
            end = pd.datetime.now().strftime('%Y-%m-%d')

        if start is None:
            start = pd.to_datetime(end) - pd.datetools.timedelta(days=365)
            start = start.strftime('%Y-%m-%d')

        pmap = self._parameter_map(service, invert=True)
        parameter_code = pmap[parameter]

        if service == 'ndbc':
            url = 'cwwcNDBCMet.csvp?time,{}&station="{}"&time>={}&time<={}'.format(parameter_code, feature, start, end)
            url = BASE_URL + url
            print('download data from %s' % url)
            data = pd.read_csv(url)
            if data.empty:
                raise ValueError('No Data Available')

            rename = {x: x.split()[0] for x in data.columns.tolist()}
            units = {x.split()[0]: x.split()[-1].strip('()').lower() for x in data.columns.tolist()}
            data.rename(columns=rename, inplace=True)
            data = data.set_index('time')
            data.index = pd.to_datetime(data.index)
            data.rename(columns={parameter_code: parameter})

        if service == 'coops':
            raise NotImplementedError

        save_path = os.path.join(save_path, BASE_PATH, service)
        save_path = os.path.join(save_path, dataset)
        metadata = {
            'save_path': save_path,
            'file_format': 'timeseries-hdf5',
            'datatype': 'timeseries',
            'timezone': units['time'],
            'parameter': parameter,
            'units': units[parameter_code],
            'service_id': 'svc://noaa:{}/{}'.format(service, feature)
        }

        # save data to disk
        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        io.write(save_path, data, metadata)
        del metadata['service_id']

        return metadata

    def _download_options(self, service, fmt):
        if fmt == 'smtk':
            parameters = sorted(self._parameter_map(service).values())
            parameters = [(p.capitalize(), p) for p in parameters]
            schema = util.build_smtk('start_end.sbt',
                                     title='Noaa Coastwatch Download Options',
                                     parameters=parameters)

        if fmt == 'json-schema':
            schema = {
                "title": "NOAA Download Options",
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
                },
            }
        return schema
