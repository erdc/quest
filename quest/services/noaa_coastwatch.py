"""QUEST wrapper for NCDC GHCN and GSOD Services."""
import os
import datetime

import pandas as pd
import param

from ..util.log import logger
from .base import WebProviderBase, ServiceBase
from .. import util

BASE_PATH = 'noaa'
BASE_URL = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/'


# noaa_url = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/nosCoopsCA.csvp?stationID%2CstationName%2CdateEstablished%2Clongitude%2Clatitude'


class NoaaServiceBase(ServiceBase):
    BASE_URL = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/'
    start = param.Date(default=lambda: None, doc='start date')
    end = param.Date(default=lambda: None, doc='end date')
    smtk_template = 'start_end.sbt'

    @property
    def metadata(self):
        return {
            'display_name': self.display_name,
            'description': self.description,
            'service_type': self.service_type,
            'parameters': list(self._parameter_map.values()),
            'unmapped_parameters_available': self.unmapped_parameters_available,
            'geom_type': self.geom_type,
            'datatype': self.datatype,
            'geographical_areas': self.geographical_areas,
            'bounding_boxes': self.bounding_boxes
        }

    @property
    def parameters(self):
        return {
            'parameters': list(self._parameter_map.values()),
            'parameter_codes': list(self._parameter_map.keys())
        }

    @property
    def features(self):
        features = self._get_features()
        return features.drop_duplicates()

    def _get_features(self):
        raise NotImplementedError()
    
    @property
    def feature(self):
        return self._feature

    @property
    def parameter_code(self):
        pmap = self.parameter_map(invert=True)
        return pmap[self.parameter]

    @property
    def url(self):
        raise NotImplementedError()

    def parameter_map(self, invert=False):
        pmap = self._parameter_map

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def __call__(self, feature, file_path, dataset, **params):
        p = param.ParamOverrides(self, params)
        self._feature = feature

        if dataset is None:
            dataset = 'station-' + feature

        # end = p.end or pd.datetime.now().strftime('%Y-%m-%d')
        #
        # start = p.start
        # if p.start is None:
        #     start = pd.to_datetime(end) - datetime.timedelta(days=365)
        #     start = start.strftime('%Y-%m-%d')


        try:
            url = self.url
            logger.info('downloading data from %s' % url)
            data = pd.read_csv(url)

            if data.empty:
                raise ValueError('No Data Available')

            rename = {x: x.split()[0] for x in data.columns.tolist()}
            units = {x.split()[0]: x.split()[-1].strip('()').lower() for x in data.columns.tolist()}
            data.rename(columns=rename, inplace=True)
            data = data.set_index('time')
            data.index = pd.to_datetime(data.index)
            data.rename(columns={self.parameter_code: self.parameter})

            file_path = os.path.join(file_path, BASE_PATH, service, dataset, '{0}.h5'.format(dataset))

            metadata = {
                'file_path': file_path,
                'file_format': 'timeseries-hdf5',
                'datatype': 'timeseries',
                'parameter': p.parameter,
                'unit': units[self.parameter_code],
                'service_id': 'svc://noaa:{}/{}'.format(self.service_name, feature)
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


class NoaaServiceBaseNDBC(NoaaServiceBase):
    service_name = 'ndbc'
    display_name = 'NOAA National Data Buoy Center'
    description = 'NDBC Standard Meteorological Buoy Data'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-177.75, -27.705, 179.001, 71.758],
    ]
    _parameter_map = {
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
        
    parameter = param.ObjectSelector(default=None, doc='parameter', objects=sorted(_parameter_map.values()))

    @property
    def url(self):
        url = 'cwwcNDBCMet.csvp?time,{}&station="{}"&time>={}&time<={}' \
            .format(self.parameter_code, self.feature, self.start, self.end)
        return self.BASE_URL + url

    def _get_features(self):
        ndbc_url = self.BASE_URL + 'cwwcNDBCMet.csvp?station%2Clongitude%2Clatitude'
        df = pd.read_csv(ndbc_url)
        df.rename(columns={
            'station': 'service_id',
            'longitude (degrees_east)': 'longitude',
            'latitude (degrees_north)': 'latitude'
        }, inplace=True)

        df['service_id'] = df['service_id'].apply(str)  # converts ints to strings
        df.index = df['service_id']
        df['display_name'] = df['service_id']

        return df


class NoaaServiceBaseCoopsMet(NoaaServiceBase):
    service_name = 'coops-meteorological'
    display_name = 'NOAA COOPS'
    description = 'Center for Operational Oceanographic Products and Services'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {
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
    _location_id_map = {
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

    parameter = param.ObjectSelector(default=None, doc='parameter', objects=sorted(_parameter_map.values()))

    @property
    def url(self):
        # start = pd.to_datetime(end) - datetime.timedelta(days=28)
        # start = start.strftime('%Y-%m-%d')

        location = self._location_id_map[self.parameter_code]
        url = 'nosCoops{}.csvp?time,{}&stationID="{}"&time>={}&time<={}' \
            .format(location, self.parameter_code, self.feature, self.start, self.end)

        return self.BASE_URL + url

    def _get_features(self):
        # hard coding for now
        dataset_Ids = ['nosCoopsCA', 'nosCoopsMW', 'nosCoopsMRF', 'nosCoopsMV', 'nosCoopsMC',
                       'nosCoopsMAT', 'nosCoopsMRH', 'nosCoopsMWT', 'nosCoopsMBP']

        coops_url = [self.BASE_URL + '{}.csvp?stationID%2Clongitude%2Clatitude'.format(id) for id in dataset_Ids]
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

        return df


class NoaaServiceBaseCoopsWater(NoaaServiceBase):
    service_name = 'coops-water'
    display_name = 'NOAA COOPS'
    description = 'Center for Operational Oceanographic Products and Services'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {
                'waterLevel': 'sea_surface_height_amplitude',
                'predictedWL': 'predicted_waterLevel',
            }
    _location_id_map = {
                'waterLevel': 'WL',
                'predictedWL': 'WLTP',
            }
    _datum_map = {
        'DHQ': 'Mean Diurnal High Water Inequality',
        'DLQ': 'Mean Diurnal Low Water Inequality',
        'DTL': 'Mean Diurnal Tide L0evel',
        'GT': 'Great Diurnal Range',
        'HWI': 'Greenwich High Water Interval( in Hours)',
        'LWI': 'Greenwich Low Water Interval( in Hours)',
        'MHHW': 'Mean Higher - High Water',
        'MHW': 'Mean High Water',
        'MLLW': 'Mean Lower_Low Water',
        'MLW': 'Mean Low Water',
        'MN': 'Mean Range of Tide',
        'MSL': 'Mean Sea Level',
        'MTL': 'Mean Tide Level',
        'NAVD': 'North American Vertical Datum',
        'STND': 'Station Datum'
    }

    parameter = param.ObjectSelector(default=None, doc='parameter', objects=sorted(_parameter_map.values()))
    quality = param.ObjectSelector(default='R', doc='quality', objects=['Preliminary', 'Verified', 'R'])
    interval = param.ObjectSelector(default='6', doc='time interval', objects=['6', '60'])
    datum = param.ObjectSelector(default='Mean Lower_Low Water', doc='datum', objects=sorted(_datum_map.values()))

    @property
    def url(self):
        location = self._location_id_map[self.parameter_code]
        quality = self.quality[0].capitalize() if self.parameter_code == 'waterLevel' else ''
        datum = self._datum_map[self.datum]

        # start = pd.to_datetime(end) - datetime.timedelta(days=28)
        # start = start.strftime('%Y-%m-%d')

        url = 'nosCoops{}{}{}.csvp?time,{}&stationID="{}"&time>={}&time<={}&datum="{}"' \
            .format(location, quality, self.interval, self.parameter_code, self.feature, self.start, self.end, datum)

        return self.BASE_URL + url

    def _get_features(self):
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

        return df


class NoaaProvider(WebProviderBase):
    service_base_class = NoaaServiceBase
    display_name = 'NOAA Coastwatch ERDDAP Web Services'
    description = 'Services available from NOAA'
    organization_name = 'National Oceanic and Atmospheric Administration'
    organization_abbr = 'NOAA'
