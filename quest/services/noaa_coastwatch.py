"""QUEST wrapper for NCDC GHCN and GSOD Services."""
from .base import WebServiceBase
from .. import util
import pandas as pd
import os
from ..util.log import logger
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
            'coops-meteorological': {
                'display_name': 'NOAA COOPS',
                'description': 'Center for Operational Oceanographic Products '
                               'and Services',
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('coops-meteorological').values()),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes': [
                    [-180, -90, 180, 90],
                ],
            },
            'coops-water': {
                'display_name': 'NOAA COOPS',
                'description': 'Center for Operational Oceanographic Products '
                               'and Services',
                'service_type': 'geo-discrete',
                'parameters': list(self._parameter_map('coops-water').values()),
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
                'station': 'service_id',
                'longitude (degrees_east)': 'longitude',
                'latitude (degrees_north)': 'latitude'
                }, inplace=True)

            df['service_id'] = df['service_id'].apply(str)  # converts ints to strings
            df.index = df['service_id']
            df['display_name'] = df['service_id']

        if service == 'coops-meteorological':
            # hard coding for now
            dataset_Ids = ['nosCoopsCA', 'nosCoopsMW', 'nosCoopsMRF', 'nosCoopsMV', 'nosCoopsMC',
                           'nosCoopsMAT', 'nosCoopsMRH', 'nosCoopsMWT', 'nosCoopsMBP']

            coops_url = [BASE_URL + '{}.csvp?stationID%2Clongitude%2Clatitude'.format(id) for id in dataset_Ids]
            df = pd.concat([pd.read_csv(f) for f in coops_url])

            df.rename(columns={
                'stationID': 'service_id',
                'longitude (degrees_east)': 'longitude',
                'parameter': 'parameters',
                'latitude (degrees_north)': 'latitude'
            }, inplace=True)

            df['service_id'] = df['service_id'].apply(str)  # converts ints to strings
            df.index = df['service_id']
            df['display_name'] = df['service_id']

        if service == 'coops-water':
            # hard coding for now
            dataset_Ids = ['nosCoopsWLV6', 'nosCoopsWLR6', 'nosCoopsWLTP6', 'nosCoopsWLV60',
                           'nosCoopsWLVHL', 'nosCoopsWLTP60', 'nosCoopsWLTPHL']

            coops_url = [BASE_URL + '{}.csvp?stationID%2Clongitude%2Clatitude'.format(id) for id in dataset_Ids]
            df = pd.concat([pd.read_csv(f) for f in coops_url])

            df.rename(columns={
                'stationID': 'service_id',
                'longitude (degrees_east)': 'longitude',
                'latitude (degrees_north)': 'latitude'
            }, inplace=True)

            df['service_id'] = df['service_id'].apply(str)  # converts ints to strings
            df.index = df['service_id']
            df['display_name'] = df['service_id']



        return df.drop_duplicates()

    def _get_parameters(self, service, features=None):
        # hardcoding for now
        if service == 'ndbc':
            parameters = {
                'parameters': list(self._parameter_map('ndbc').values()),
                'parameter_codes': list(self._parameter_map('ndbc').keys())
            }

        if service == 'coops-meteorological':
            parameters = {
                'parameters': list(self._parameter_map('coops-meteorological').values()),
                'parameter_codes': list(self._parameter_map('coops-meteorological').keys())
            }
        if service == 'coops-water':
            parameters = {
                'parameters': list(self._parameter_map('coops-water').values()),
                'parameter_codes': list(self._parameter_map('coops-water').keys())
            }

        return parameters

    def _datasetId_map(self,service,parameter, invert=False):

        if service == 'coops-meteorological':
            dmap = {
                'CS': 'CA',
                'CD': 'CA',
                'WS': 'MW',
                'WD': 'MW',
                'WG': 'MW',
                'RF': 'MRF',
                'Vis': 'MV',
                'CN': 'MC',
                'AT': 'MAT',
                'RH': 'MRH',
                'WT': 'MWT',
                'BP': 'MBP'
                 }

        if service == 'coops-water':
            dmap = {
                'waterLevel': 'WL',
                'predictedWL': 'WLTP',
            }

        return dmap[parameter]

        if invert:
            pmap = {v: k for k, v in pmap.items()}

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

        if service == 'coops-meteorological':
            pmap = {
                'CS': 'sea_water_speed',
                'CD': 'direction_of_sea_water_velocity',
                'WS': 'wind_speed',
                'WD': 'wind_from_direction',
                'WG': 'wind_speed_from_gust',
                'RF': 'collective_rainfall',
                'Vis': 'visibility_in_air',
                'CN': 'sea_water_electric_conductivity',
                'AT': 'air_temperature',
                'RH': 'relative_humidity',
                'WT': 'sea_water_temperature',
                'BP': 'barometric_pressure',
            }
        if service == 'coops-water':
            pmap = {
                'waterLevel': 'sea_surface_height_amplitude',
                'predictedWL': 'predicted_waterLevel',
            }

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def _download(self, service, feature, file_path, dataset,
                  parameter, start=None, end=None, quality='R', interval='6', datum='MLLW'):

        if dataset is None:
            dataset = 'station-' + feature

        if end is None:
            end = pd.datetime.now().strftime('%Y-%m-%d')

        if start is None:
            start = pd.to_datetime(end) - pd.datetools.timedelta(days=365)
            start = start.strftime('%Y-%m-%d')

        pmap = self._parameter_map(service, invert=True)
        parameter_code = pmap[parameter]
        try:
            if service == 'ndbc':
                url = 'cwwcNDBCMet.csvp?time,{}&station="{}"&time>={}&time<={}'.format(parameter_code, feature, start, end)
                url = BASE_URL + url
                logger.info('downloading data from %s' % url)
                data = pd.read_csv(url)
                if data.empty:
                    raise ValueError('No Data Available')

                rename = {x: x.split()[0] for x in data.columns.tolist()}
                units = {x.split()[0]: x.split()[-1].strip('()').lower() for x in data.columns.tolist()}
                data.rename(columns=rename, inplace=True)
                data = data.set_index('time')
                data.index = pd.to_datetime(data.index)
                data.rename(columns={parameter_code: parameter})

            if service == 'coops-meteorological':

                start = pd.to_datetime(end) - pd.datetools.timedelta(days=28)
                start = start.strftime('%Y-%m-%d')

                location = self._datasetId_map(service, parameter_code)
                url = 'nosCoops{}.csvp?time,{}&stationID="{}"&time>={}&time<={}'.format(location,parameter_code,feature, start, end)
                url = BASE_URL + url
                logger.info('downloading data from %s' % url)
                data = pd.read_csv(url)
                if data.empty:
                    raise ValueError('No Data Available')

                rename = {x: x.split()[0] for x in data.columns.tolist()}
                units = {x.split()[0]: x.split()[-1].strip('()').lower() for x in data.columns.tolist()}
                data.rename(columns=rename, inplace=True)
                data = data.set_index('time')
                data.index = pd.to_datetime(data.index)
                data.rename(columns={parameter_code: parameter})

            if service == 'coops-water':
                if parameter_code == 'waterLevel':
                    location = self._datasetId_map(service, parameter_code) + quality[0].capitalize() + interval
                else:
                    location=self._datasetId_map(service, parameter_code) + interval

                start = pd.to_datetime(end) - pd.datetools.timedelta(days=28)
                start = start.strftime('%Y-%m-%d')

                url = 'nosCoops{}.csvp?time,{}&stationID="{}"&time>={}&time<={}&datum="{}"'.format(location,parameter_code,feature, start,end, datum)
                url = BASE_URL + url
                logger.info('downloading data from %s' % url)
                data = pd.read_csv(url)
                if data.empty:
                    raise ValueError('No Data Available')

                rename = {x: x.split()[0] for x in data.columns.tolist()}
                units = {x.split()[0]: x.split()[-1].strip('()').lower() for x in data.columns.tolist()}
                data.rename(columns=rename, inplace=True)
                data = data.set_index('time')
                data.index = pd.to_datetime(data.index)
                data.rename(columns={parameter_code: parameter})

            file_path = os.path.join(file_path, BASE_PATH, service)
            file_path = os.path.join(file_path, dataset)
            metadata = {
                'file_path': file_path,
                'file_format': 'timeseries-hdf5',
                'datatype': 'timeseries',
                'parameter': parameter,
                'unit': units[parameter_code],
                'service_id': 'svc://noaa:{}/{}'.format(service, feature)
            }

            # save data to disk
            io = util.load_drivers('io', 'timeseries-hdf5')
            io = io['timeseries-hdf5'].driver
            io.write(file_path, data, metadata)
            del metadata['service_id']

            return metadata

        except Exception as error:
            if str(error) == "HTTP Error 500: Internal Server Error":
                raise ValueError('No Data Available')

    def _download_options(self, service, fmt):
        if service == 'ndbc' or service == 'coops-meteorological':

            if fmt == 'smtk':
                parameters = sorted(self._parameter_map(service).values())
                parameters = [(p.capitalize(), p) for p in parameters]
                schema = util.build_smtk('download_options',
                                         'start_end.sbt',
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

        if service == 'coops-water':
            if fmt == 'smtk':
                parameters = sorted(self._parameter_map(service).values())
                parameters = [(p.capitalize(), p) for p in parameters]
                schema = util.build_smtk('download_options',
                                         'start_end.sbt',
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
                        "quality": {
                            "type": "string",
                            "description": "quality",
                            "options": ['Preliminary','Verified'],
                        },
                        "interval": {
                            "type": "string",
                            "description": "time interval",
                            "options": ['6', '60'],
                        },
                        "datum": {  # temporary hard coding
                            "type": "string",
                            "description": "time interval",
                            "options": [
                                        {'DHQ':'Mean Diurnal High Water Inequality'},
                                        {'DLQ':'Mean Diurnal Low Water Inequality'},
                                        {'DTL':'Mean Diurnal Tide L0evel'},
                                        {'GT':'Great Diurnal Range'},
                                        {'HWI':'Greenwich High Water Interval( in Hours)'},
                                        {'LWI':'Greenwich Low Water Interval( in Hours)'},
                                        {'MHHW':'Mean Higher - High Water'},
                                        {'MHW':'Mean High Water'},
                                        {'MLLW':'Mean Lower_Low Water'},
                                        {'MLW':'Mean Low Water'},
                                        {'MN':'Mean Range of Tide'},
                                        {'MSL':'Mean Sea Level'},
                                        {'MTL':'Mean Tide Level'},
                                        {'NAVD''North American Vertical Datum'},
                                        {'STND':'Station Datum'},
                                        ]
                        },
                    },
                }

        return schema
