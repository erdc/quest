import os

import param
import pandas as pd
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

from quest.util.log import logger
from quest.static import ServiceType, GeomType, DataType
from quest.plugins import ProviderBase, TimePeriodServiceBase, load_plugins


class NoaaServiceBase(TimePeriodServiceBase):
    BASE_URL = 'http://coastwatch.pfeg.noaa.gov/erddap/tabledap/'
    BASE_PATH = 'noaa'

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

    def search_catalog(self, **kwargs):
        raise NotImplementedError()
        # TODO drop duplicates?
    
    @property
    def catalog_id(self):
        return self._catalog_id

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

    def download(self, catalog_id, file_path, dataset, **kwargs):
        p = param.ParamOverrides(self, kwargs)
        self.parameter = p.parameter
        self.end = pd.to_datetime(p.end)
        self.start = pd.to_datetime(p.start)
        self._catalog_id = catalog_id

        if dataset is None:
            dataset = 'station-' + catalog_id

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

            file_path = os.path.join(file_path, self.BASE_PATH, self.service_name, dataset, '{0}.h5'.format(dataset))

            metadata = {
                'file_path': file_path,
                'file_format': 'timeseries-hdf5',
                'datatype': DataType.TIMESERIES,
                'parameter': p.parameter,
                'unit': units[self.parameter_code],
                'service_id': 'svc://noaa:{}/{}'.format(self.service_name, catalog_id)
            }

            # save data to disk
            io = load_plugins('io', 'timeseries-hdf5')['timeseries-hdf5']
            io.write(file_path, data, metadata)
            del metadata['service_id']

            return metadata

        except HTTPError as error:
            if error.code == 500:
                raise ValueError('No Data Available')
            elif error.code == 400:
                raise ValueError('Bad Request')
            else:
                raise error

    def _format_url(self, dataset_id, file_type='csvp', variables=None, start_time=None, end_time=None, **kwargs):
        query = {k: '"{}"'.format(v) for k, v in kwargs.items()}
        if start_time is not None and end_time is not None:
            query.update({'time>': start_time,
                          'time<': end_time})
        query = urlencode(query)
        if variables is not None:
            variables = quote(','.join(variables))

        if variables is not None and query:
            variables += '&'

        url_selector = '{dataset_id}.{file_type}?{variables}{query}'.format(
            dataset_id=dataset_id,
            file_type=file_type,
            variables=variables,
            query=query
        )

        return self.BASE_URL + url_selector


class NoaaServiceNDBC(NoaaServiceBase):
    service_name = 'ndbc'
    display_name = 'NOAA National Data Buoy Center'
    description = 'NDBC Standard Meteorological Buoy Data'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
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

    _dataset_id = 'cwwcNDBCMet'
        
    parameter = param.ObjectSelector(
        default=None,
        doc='parameter',
        precedence=1,
        objects=sorted(_parameter_map.values())
    )

    @property
    def url(self):

        variables = 'time', self.parameter_code

        return self._format_url(dataset_id=self._dataset_id, variables=variables,
                                station=self.catalog_id, start_time=self.start, end_time=self.end)

    def search_catalog(self, **kwargs):
        variables = 'station', 'longitude', 'latitude'
        df = pd.read_csv(self._format_url(dataset_id=self._dataset_id, variables=variables))
        df.rename(columns={
            'station': 'service_id',
            'longitude (degrees_east)': 'longitude',
            'latitude (degrees_north)': 'latitude'
        }, inplace=True)

        df['service_id'] = df['service_id'].apply(str)  # converts ints to strings
        df.index = df['service_id']
        df['display_name'] = df['service_id']

        return df


class NoaaServiceCoopsMet(NoaaServiceBase):
    service_name = 'coops-meteorological'
    display_name = 'NOAA COOPS Met'
    description = 'Center for Operational Oceanographic Products and Services'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
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

    parameter = param.ObjectSelector(
        default=None,
        doc='parameter',
        precedence=1,
        objects=sorted(_parameter_map.values())
    )

    @property
    def url(self):

        location = self._location_id_map[self.parameter_code]
        dataset_id = 'nosCoops{}'.format(location)
        variables = 'time', self.parameter_code

        return self._format_url(dataset_id=dataset_id, variables=variables,
                                stationID=self.catalog_id, start_time=self.start, end_time=self.end)

    def search_catalog(self, **kwargs):
        # hard coding for now
        dataset_services = ['nosCoopsCA', 'nosCoopsMW', 'nosCoopsMRF', 'nosCoopsMV', 'nosCoopsMC',
                            'nosCoopsMAT', 'nosCoopsMRH', 'nosCoopsMWT', 'nosCoopsMBP']
        variables = ['stationID', 'longitude', 'latitude']

        # coops_url = [self.BASE_URL + '{}.csvp?stationID%2Clongitude%2Clatitude'.format(id) for id in dataset_Ids]
        coops_url = [self._format_url(dataset_id=dataset_id, variables=variables) for dataset_id in dataset_services]
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


class NoaaServiceCoopsWater(NoaaServiceBase):
    service_name = 'coops-water'
    display_name = 'NOAA COOPS Water'
    description = 'Center for Operational Oceanographic Products and Services'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
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

    parameter = param.ObjectSelector(
        default=None,
        doc='parameter',
        precedence=1,
        objects=sorted(_parameter_map.values())
    )
    quality = param.ObjectSelector(
        default='R',
        doc='quality',
        precedence=4,
        objects=['Preliminary', 'Verified', 'R']
    )
    interval = param.ObjectSelector(
        default='6',
        doc='time interval',
        precedence=5,
        objects=['6', '60']
    )
    datum = param.ObjectSelector(
        default='Mean Lower_Low Water',
        precedence=6,
        doc='datum',
        objects=sorted(_datum_map.values())
    )

    @property
    def url(self):
        location = self._location_id_map[self.parameter_code]
        quality = self.quality[0].capitalize() if self.parameter_code == 'waterLevel' else ''
        datum = {v: k for k, v in self._datum_map.items()}[self.datum]
        dataset_id = 'nosCoops{}{}{}'.format(location, quality, self.interval)

        variables = 'time', self.parameter_code

        return self._format_url(dataset_id=dataset_id, variables=variables,
                                stationID=self.catalog_id, datum=datum,
                                start_time=self.start, end_time=self.end)

    def search_catalog(self, **kwargs):
        # hard coding for now
        dataset_services = ['nosCoopsWLV6', 'nosCoopsWLR6', 'nosCoopsWLTP6', 'nosCoopsWLV60',
                            'nosCoopsWLVHL', 'nosCoopsWLTP60', 'nosCoopsWLTPHL']

        variables = 'stationID', 'longitude', 'latitude'

        coops_url = [self._format_url(dataset_id=dataset_id, variables=variables) for dataset_id in
                     dataset_services]
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


class NoaaProvider(ProviderBase):
    service_list = [NoaaServiceNDBC, NoaaServiceCoopsMet, NoaaServiceCoopsWater]
    display_name = 'NOAA Coastwatch ERDDAP Web Services'
    description = 'Services available from NOAA'
    organization_name = 'National Oceanic and Atmospheric Administration'
    organization_abbr = 'NOAA'
    name = 'noaa-coast'
