import os

import param
import pandas as pd
from ulmo.ncdc import ghcn_daily, gsod

from quest.static import ServiceType, GeomType, DataType
from quest.plugins import ProviderBase, TimePeriodServiceBase, load_plugins


BASE_PATH = 'ncdc'


class NcdcServiceBase(TimePeriodServiceBase):

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
    def parameter_code(self):
        pmap = self.parameter_map(invert=True)
        return pmap[self.parameter]

    def search_catalog(self, **kwargs):
        catalog_entries = self._search_catalog()

        # remove locations with invalid coordinates
        valid = pd.notnull(catalog_entries.latitude) & pd.notnull(catalog_entries.longitude)
        catalog_entries = catalog_entries[valid]
        catalog_entries.rename(columns={
            'name': 'display_name',
            'longitude': 'longitude',
            'latitude': 'latitude'
        }, inplace=True)

        # drop columns that just duplicate information already in the service_id
        catalog_entries.drop(labels=['id', 'network_id', 'WBAN', 'USAF'], axis=1, inplace=True, errors='ignore')

        return catalog_entries

    @property
    def catalog_entry(self):
        return self._catalog_entry

    @property
    def data(self):
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
        self._catalog_entry = catalog_id

        if dataset is None:
            dataset = 'station-' + catalog_id

        # if end is None:
        #     end = pd.datetime.now().strftime('%Y-%m-%d')
        #
        # if start is None:
        #     start = pd.to_datetime(end) - pd.datetools.timedelta(days=30)
        #     start = start.strftime('%Y-%m-%d')

        file_path = os.path.join(file_path, BASE_PATH, self.service_name, dataset, '{0}.h5'.format(dataset))

        metadata = {
            'file_path': file_path,
            'file_format': 'timeseries-hdf5',
            'datatype': DataType.TIMESERIES,
            'parameter': self.parameter,
            'unit': self._unit_map[self.parameter],
            'service_id': 'svc://ncdc:{}/{}'.format(self.service_name, catalog_id)
        }

        # save data to disk
        io = load_plugins('io', 'timeseries-hdf5')['timeseries-hdf5']
        io.write(file_path, self.data, metadata)
        del metadata['service_id']

        return metadata


class NcdcServiceGhcnDaily(NcdcServiceBase):
    service_name = 'ghcn-daily'
    display_name = 'NCDC GHCN Daily'
    description = 'Daily Meteorologic Data from the Global Historic Climate Network'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {
        'PRCP': 'rainfall:daily:total',
        'SNOW': 'snowfall:daily:total',
        'SNWD': 'snow_depth:daily:total',
        'TMAX': 'air_temperature:daily:total',
        'TMIN': 'air_temperature:daily:minimum',
        'TAVG': 'air_temperature:daily:mean'
    }
    _unit_map = {
        'rainfall:daily:total': '0.1*mm',
        'snowfall:daily:total': 'mm',
        'snow_depth:daily:total': 'mm',
        'air_temperature:daily:total': '0.1*degC',
        'air_temperature:daily:minimum': '0.1*degC',
        'air_temperature:daily:mean': '0.1*degC',
    }

    parameter = param.ObjectSelector(default=None, doc='parameter', precedence=1, objects=sorted(_parameter_map.values()))

    @property
    def data(self):
        data = ghcn_daily.get_data(self.catalog_entry,
                                   elements=self.parameter_code,
                                   as_dataframe=True)  # [parameter_code]
        if not data or data[self.parameter_code].empty:
            raise ValueError('No Data Available')

        data = data[self.parameter_code]

        data = data[self.start_string:self.end_string]
        if data.empty:
            raise ValueError('No Data Available')
        data.rename(columns={'value': self.parameter}, inplace=True)

        return data

    def _search_catalog(self, **kwargs):
        return ghcn_daily.get_stations(as_dataframe=True)


class NcdcServiceGsod(NcdcServiceBase):
    service_name = 'gsod'
    display_name = 'NCDC GSOD'
    description = 'Daily Meteorologic Data from the Global Summary of the Day'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90]
    ]
    _parameter_map = {
        'precip': 'rainfall:daily:total',
        'snow_depth': 'snow_depth:daily:total',
        'max_temp': 'air_temperature:daily:max',
        'min_temp': 'air_temperature:daily:min',
    }
    _unit_map = {
        'rainfall:daily:total': '0.01*inches',
        'snow_depth:daily:total': '0.01*inches',
        'air_temperature:daily:max': '0.1*degF',
        'air_temperature:daily:min': '0.1*degF',
        'air_temperature:daily:min': '0.1*degF',
    }
    parameter = param.ObjectSelector(default=None, doc='parameter', precedence=1, objects=sorted(_parameter_map.values()))

    @property
    def data(self):
        data = gsod.get_data(self.catalog_entry, start=self.start, end=self.end,
                             parameters=self.parameter_code)

        if not data or not data[self.catalog_entry]:
            raise ValueError('No Data Available')

        data = data[self.catalog_entry]
        data = pd.DataFrame(data)
        if data.empty:
            raise ValueError('No Data Available')

        data = data.set_index('date')
        data.index = pd.PeriodIndex(data.index, freq='D')
        data.rename(columns={self.parameter_code: self.parameter}, inplace=True)

        return data

    def _search_catalog(self, **kwargs):
        catalog_entries = gsod.get_stations()
        catalog_entries = pd.DataFrame.from_dict(catalog_entries, orient='index')
        return catalog_entries


class NcdcProvider(ProviderBase):
    service_list = [NcdcServiceGhcnDaily, NcdcServiceGsod]
    display_name = 'NCDC Web Services'
    description = 'Services available through the NCDC'
    organization_name = 'National Climatic Data Center'
    organization_abbr = 'NCDC'
    name = 'noaa-ncdc'
