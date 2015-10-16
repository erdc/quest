"""DSL wrapper for USGS NWIS Services

"""
from .base import WebServiceBase
import pickle
import pandas as pd
import os
import requests
from ulmo.ncdc import ghcn_daily, gsod
from ulmo.ncdc.ghcn_daily.core import _get_inventory as _get_ghcn_inventory
from .. import util


collections_url = 'https://cmr.earthdata.nasa.gov/search/collections.json?short_name=%s'

granules_url = 'https://cmr.earthdata.nasa.gov/search/granules.json?short_name=%s&page_size=1000&page_num=%s'

def _read_metadata(short_name):
    #return requests.get(collections_url % short_name).json()['feed']['entry'][0]
    if short_name=='SRTMGL3N':
        metadata = {
            u'archive_center': u'LPDAAC',
            u'boxes': [u'-56 -180 60 180'],
            u'browse_flag': False,
            u'coordinate_system': u'CARTESIAN',
            u'data_center': u'LPDAAC_ECS',
            u'dataset_id': u'NASA Shuttle Radar Topography Mission Global 3 arc second number V003',
            u'id': u'C204582037-LPDAAC_ECS',
            u'links': [{u'href': u'http://dx.doi.org/10.5067/MEaSUREs/SRTM/SRTMGL3N.003',
              u'hreflang': u'en-US',
              u'rel': u'http://esipfed.org/ns/fedsearch/1.1/metadata#',
              u'title': u'Data set landing page at the LP DAAC (MiscInformation)'}],
            u'online_access_flag': False,
            u'orbit_parameters': {},
            u'original_format': u'ECHO10',
            u'processing_level_id': u'3',
            u'short_name': u'SRTMGL3N',
            u'summary': u'NASA Shuttle Radar Topography Mission Global 3 arc second number',
            u'time_end': u'2000-02-21T23:59:59.000Z',
            u'time_start': u'2000-02-11T00:00:00.000Z',
            u'title': u'NASA Shuttle Radar Topography Mission Global 3 arc second number V003',
            u'updated': u'2015-09-02T10:31:07.438Z',
            u'version_id': u'003'
        }

    if short_name=='SRTMGL30':
        metadata = {
            u'archive_center': u'LPDAAC',
            u'boxes': [u'-56 -180 60 180'],
            u'browse_flag': False,
            u'coordinate_system': u'CARTESIAN',
            u'data_center': u'LPDAAC_ECS',
            u'dataset_id': u'NASA Shuttle Radar Topography Mission Global 30 arc second V002',
            u'id': u'C204582036-LPDAAC_ECS',
            u'links': [{u'href': u'http://dx.doi.org/10.5067/MEaSUREs/SRTM/SRTMGL30.002',
              u'hreflang': u'en-US',
              u'rel': u'http://esipfed.org/ns/fedsearch/1.1/metadata#',
              u'title': u'Data set landing page at the LP DAAC (MiscInformation)'}],
            u'online_access_flag': False,
            u'orbit_parameters': {},
            u'original_format': u'ECHO10',
            u'processing_level_id': u'3',
            u'short_name': u'SRTMGL30',
            u'summary': u'NASA Shuttle Radar Topography Mission Global 30 arc second',
            u'time_end': u'2000-02-21T23:59:59.000Z',
            u'time_start': u'2000-02-11T00:00:00.000Z',
            u'title': u'NASA Shuttle Radar Topography Mission Global 30 arc second V002',
            u'updated': u'2015-09-02T10:31:07.011Z',
            u'version_id': u'002'
        }
    return metadata

def _read_granules(short_name, page_num):
    return requests.get(granules_url % (short_name, page_num)).json()['feed']['entry']

class NasaService(WebServiceBase):
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
        for service, short_name in self._service_dict().iteritems():
            metadata = _read_metadata(short_name)
            metadata['display_name'] = metadata.pop('title')
            metadata['description'] = metadata.pop('summary')
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
            'srtm-3-arc-second': 'SRTMGL3N', 
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
        features.index = features['id']
        features['geom_type'] = 'Polygon'
        features['geom_coords'] = features['boxes'].apply(lambda x: [util.bbox2poly(*x[0].split(), reverse_order=True)])
        coords = features['geom_coords'].apply(lambda x: pd.np.array(x).mean(axis=1))
        features['longitude'] = coords.apply(lambda x: x.flatten()[0])
        features['latitude'] = coords.apply(lambda x: x.flatten()[1])
        #features['download_url'] = features['links'].apply(lambda x: link['href'] for link in x if link['type']=='application/zip')
        return features

    def _get_parameters(self, service, features=None):
        return {
            'parameters': ['elevation'],
            'parameter_codes': ['elevation'],
        }

    def _download_data(self, feature, parameter, path, start=None, end=None, period=None):
        pass
