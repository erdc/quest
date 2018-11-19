import os

from ulmo.usgs import ned

from quest import util
from quest.static import ServiceType, DataType, GeomType
from quest.plugins import ProviderBase, SingleFileServiceBase


DEFAULT_FILE_PATH = os.path.join('usgs','ned')
CACHE_FILE = 'ned_%s_metadata.json'


class UsgsNedServiceBase(SingleFileServiceBase):
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = False
    geom_type = GeomType.POLYGON
    datatype = DataType.RASTER
    geographical_areas = ['Alaska', 'USA', 'Hawaii']
    bounding_boxes = [[-180, -90, 180, 90]]
    _parameter_map = {
        'elevation': 'elevation'
    }

    def search_catalog(self, **kwargs):
        service = self._description
        catalog_entries = util.to_geodataframe(
            ned.get_raster_availability(service, (-180, -90, 180, 90))
        )
        if catalog_entries.empty:
            return catalog_entries

        catalog_entries['parameters'] = 'elevation'
        catalog_entries['filename'] = catalog_entries['download url'].apply(lambda x: x.split('/')[-1])
        catalog_entries['reserved'] = catalog_entries.apply(
            lambda x: {'download_url': x['download url'],
                       'filename': x['filename'],
                       'file_format': 'raster-gdal',
                       'extract_from_zip': '.img',
                       }, axis=1)

        catalog_entries.drop(labels=['filename', 'download url', 'format'], axis=1, inplace=True)

        return catalog_entries.rename(columns={'name': 'display_name'})


class UsgsNedServiceAlaska(UsgsNedServiceBase):
    service_name = 'alaska-2-arc-second'
    _description = 'Alaska 2 arc-second'
    display_name = 'USGS National Elevation Dataset {}'.format(_description)
    description = 'Retrieve USGS NED at {} resolution'.format(_description)


class UsgsNedService1ArcSec(UsgsNedServiceBase):
    service_name = '1-arc-second'
    _description = '1 arc-second'
    display_name = 'USGS National Elevation Dataset {}'.format(_description)
    description = 'Retrieve USGS NED at {} resolution'.format(_description)


class UsgsNedService13ArcSec(UsgsNedServiceBase):
    service_name = '13-arc-second'
    _description = '1/3 arc-second'
    display_name = 'USGS National Elevation Dataset {}'.format(_description)
    description = 'Retrieve USGS NED at {} resolution'.format(_description)


class UsgsNedService19ArcSec(UsgsNedServiceBase):
    service_name = '19-arc-second'
    _description = '1/9 arc-second'
    display_name = 'USGS National Elevation Dataset {}'.format(_description)
    description = 'Retrieve USGS NED at {} resolution'.format(_description)


class UsgsNedProvider(ProviderBase):
    service_list = [UsgsNedServiceAlaska, UsgsNedService1ArcSec, UsgsNedService13ArcSec, UsgsNedService19ArcSec]
    display_name = 'USGS National Elevation Dataset'
    description = 'National Elevation Dataset at several resolutions'
    organization_name = 'United States Geological Survey'
    organization_abbr = 'USGS'
    name = 'usgs-ned'
