"""QUEST wrapper for USGS NWIS Services

"""
from .base import SingleFileBase
import pandas as pd
import requests
from .. import util


collections_url = 'https://cmr.earthdata.nasa.gov/search/collections.json?short_name=%s'

granules_url = 'https://cmr.earthdata.nasa.gov/search/granules.json?short_name=%s&page_size=1000&page_num=%s'

def _read_metadata(short_name):
    # return requests.get(collections_url % short_name).json()['feed']['entry'][0]
    if short_name == 'SRTMGL3':
        metadata = {
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

    if short_name == 'SRTMGL30':
        metadata = {
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
    return metadata


def _read_granules(short_name, page_num):
    return requests.get(granules_url % (short_name, page_num)).json()['feed']['entry']


class NasaService(SingleFileBase):
    def _register(self):
        self.metadata = {
            'display_name': 'NASA Web Services',
            'description': 'Services available through the NASA',
            'organization': {
                'abbr': 'NASA',
                'name': 'National Aeronautic and Space Administration',
            },
        }

    def _get_services(self):
        services = {}
        for service, short_name in self._service_dict().items():
            metadata = _read_metadata(short_name)
            metadata['display_name'] = metadata.pop('title')
            metadata['description'] = metadata.pop('summary')
            metadata['service_type'] = 'geo-discrete'
            metadata['bounding_boxes'] = [[float(x) for x in metadata['boxes'][0].split()]]
            metadata.update({
                'parameters': ['elevation'],
                'unmapped_parameters_available': False,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide']
                })
            services[service] = metadata

        return services

    def _service_dict(self):
        return {
            'srtm-3-arc-second': 'SRTMGL3',
            'srtm-30-arc-second': 'SRTMGL30',
        }

    def _get_features(self, service):
        short_name = self._service_dict()[service]
        page_num = 0
        data = []
        while True:
            page_num += 1
            granules = _read_granules(short_name, page_num)
            if len(granules)==0:
                break

            data += granules

        features = pd.DataFrame(data)
        features.set_index('id', inplace=True)
        features['bbox'] = features['boxes'].apply(lambda x: x[0].split())
        features['bbox'] = features['bbox'].apply(lambda x: [x[i] for i in [1, 0, 3, 2]])
        features['download_url'] = features['links'].apply(
            lambda x: next(iter([link['href'] for link in x if link.get('type') == 'application/zip']), None))

        features = features.ix[~features.download_url.isnull()]
        features['reserved'] = features['download_url'].apply(lambda x: {'download_url': x, 'file_format': 'raster-gdal','extract_from_zip': '.DEM'})

        # features['_filename'] = features._download_url.apply(lambda x: x.split('/')[-1])
        # features['_extract_from_zip'] = '.DEM'
        # features['_file_format'] = 'raster-gdal'
        del features['download_url']
        del features['links']
        del features['boxes']

        return features

    def _get_parameters(self, service, features=None):
        return {
            'parameters': ['elevation'],
            #'parameter_codes': ['elevation'],
        }
