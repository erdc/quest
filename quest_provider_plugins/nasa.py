import requests
import pandas as pd
from getpass import getpass

from quest.util import log
from quest.database.database import get_db, db_session
from quest.static import ServiceType, GeomType, DataType

collections_url = 'https://cmr.earthdata.nasa.gov/search/collections.json?short_name=%s'

granules_url = 'https://cmr.earthdata.nasa.gov/search/granules.json?short_name=%s&page_size=1000&page_num=%s'

raise ValueError('This Plugin is disabled')


class NasaServiceBase(SingleFileServiceBase):
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = False
    geom_type = GeomType.POINT
    datatype = DataType.TIMESERIES
    geographical_areas = ['Worldwide']
    _parameter_map = {
        'elevation': 'elevation'
    }

    @property
    def info(self):
        return self.provider.get_user_info()

    def _read_granules(self, short_name, page_num):
        try:
            return requests.get(granules_url % (short_name, page_num), auth=(self.info['username'], self.info['password'])).json()['feed']['entry']
        except ValueError:
            return requests.get(granules_url % (short_name, page_num)).json()['feed']['entry']

    def search_catalog(self, **kwargs):

        page_num = 0
        data = []
        while True:
            page_num += 1
            granules = self._read_granules(self._short_name, page_num)
            if len(granules) == 0:
                break

            data += granules

        catalog_entries = pd.DataFrame(data)
        catalog_entries.set_index('id', inplace=True)
        catalog_entries['bbox'] = catalog_entries['boxes'].apply(lambda x: x[0].split())
        catalog_entries['bbox'] = catalog_entries['bbox'].apply(lambda x: [x[i] for i in [1, 0, 3, 2]])
        catalog_entries['download_url'] = catalog_entries['links'].apply(
            lambda x: next(iter([link['href'] for link in x if link.get('type') == 'application/zip']), None))

        catalog_entries = catalog_entries.loc[~catalog_entries.download_url.isnull()]
        catalog_entries['reserved'] = catalog_entries['download_url'].apply(lambda x: {'download_url': x, 'file_format': 'raster-gdal','extract_from_zip': '.DEM'})

        # catalog_entries['_filename'] = catalog_entries._download_url.apply(lambda x: x.split('/')[-1])
        # catalog_entries['_extract_from_zip'] = '.DEM'
        # catalog_entries['_file_format'] = 'raster-gdal'
        del catalog_entries['download_url']
        del catalog_entries['links']
        del catalog_entries['boxes']

        return catalog_entries


class NasaServiceSrtm3ArcSec(NasaServiceBase):
    service_name = 'srtm-3-arc-second'
    _short_name = 'SRTMGL3'
    _metadata = {
        'archive_center': 'LPDAAC',
        'boxes': ['-56 -180 60 180'],
        'browse_flag': False,
        'coordinate_system': 'CARTESIAN',
        'data_center': 'LPDAAC_ECS',
        'dataset_id': 'NASA Shuttle Radar Topography Mission Global 3 arc second V003',
        'id': 'C204582034-LPDAAC_ECS',
        'links': [{
            'href': 'http://dx.doi.org/10.5067/MEaSUREs/SRTM/SRTMGL3.003',
            'hreflang': 'en-US',
            'rel': 'http://esipfed.org/ns/fedsearch/1.1/metadata#',
            'title': 'Data set landing page at the LP DAAC (MiscInformation)'
        }],
        'online_access_flag': False,
        'orbit_parameters': {},
        'original_format': 'ECHO10',
        'processing_level_id': '3',
        'short_name': 'SRTMGL3',
        'summary': u"Created using a conventional 'taking looks' technique of averaging pixels to decrease the effects of speckle and increase radiometric accuracy using the original postings.",
        'time_end': '2000-02-21T23:59:59.000Z',
        'time_start': '2000-02-11T00:00:00.000Z',
        'title': 'NASA Shuttle Radar Topography Mission Global 3 arc second V003',
        'updated': '2015-09-02T10:31:06.540Z',
        'version_id': '003',
    }
    display_name = _metadata.get('title')
    description = _metadata.get('summary')
    bounding_boxes = [[float(x) for x in _metadata['boxes'][0].split()]]


class NasaServiceSrtm30ArcSec(NasaServiceBase):
    service_name = 'srtm-30-arc-second'
    _short_name = 'SRTMGL30'
    _metadata = {
        'archive_center': 'LPDAAC',
        'boxes': ['-56 -180 60 180'],
        'browse_flag': False,
        'coordinate_system': 'CARTESIAN',
        'data_center': 'LPDAAC_ECS',
        'dataset_id': 'NASA Shuttle Radar Topography Mission Global 30 arc second V002',
        'id': 'C204582036-LPDAAC_ECS',
        'links': [{
            'href': 'http://dx.doi.org/10.5067/MEaSUREs/SRTM/SRTMGL30.002',
            'hreflang': 'en-US',
            'rel': 'http://esipfed.org/ns/fedsearch/1.1/metadata#',
            'title': 'Data set landing page at the LP DAAC (MiscInformation)'
        }],
        'online_access_flag': False,
        'orbit_parameters': {},
        'original_format': 'ECHO10',
        'processing_level_id': '3',
        'short_name': 'SRTMGL30',
        'summary': 'NASA Shuttle Radar Topography Mission Global 30 arc second',
        'time_end': '2000-02-21T23:59:59.000Z',
        'time_start': '2000-02-11T00:00:00.000Z',
        'title': 'NASA Shuttle Radar Topography Mission Global 30 arc second V002',
        'updated': '2015-09-02T10:31:07.011Z',
        'version_id': '002',
    }
    display_name = _metadata.get('title')
    description = _metadata.get('summary')
    bounding_boxes = [[float(x) for x in _metadata['boxes'][0].split()]]


class NasaProvider(ProviderBase):
    service_list = [NasaServiceSrtm3ArcSec, NasaServiceSrtm30ArcSec]
    display_name = 'NASA Web Services'
    description = 'Services available through the NASA'
    organization_name = 'National Aeronautic and Space Administration'
    organization_abbr = 'NASA'

    def get_user_info(self):
        the_info = self.credentials
        return the_info

    def authenticate_me(self, **kwargs):

        username = input("Enter Username: ")
        password = getpass("Enter Password: ")

        try:
            db = get_db()
            with db_session:
                p = db.Providers.select().filter(provider=self.name).first()

                provider_metadata = {
                    'provider': self.name,
                    'username': username,
                    'password': password,
                }

                if p is None:
                    db.Providers(**provider_metadata)
                else:
                    p.set(**provider_metadata)

            return True

        except:
            log.error("Either credentials invalid or unable to connect to HydroShare.")

        return False
