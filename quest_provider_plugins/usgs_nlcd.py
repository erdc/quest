"""providers based on www.sciencebase.gov."""

import pandas as pd
import requests
from quest.plugins import ProviderBase, SingleFileServiceBase
from quest import util


class UsgsNlcdServiceBase(SingleFileServiceBase):
    service_type = 'geo-discrete'
    unmapped_parameters_available = False
    geom_type = 'polygon'
    datatype = 'discrete-raster'
    geographical_areas = ['USA']
    bounding_boxes = [[-130.232828, 21.742308, -63.672192, 52.877264]]
    _parameter_map = {
        'landcover': 'landcover'
    }

    def get_features(self, **kwargs):
        base_url = 'https://www.sciencebase.gov/catalog/items'
        params = [
            ('filter', 'tags!=tree canopy'),
            ('filter', 'tags!=Imperviousness'),
            ('filter', 'tags=GeoTIFF'),
            ('max', 1000),
            ('fields', 'webLinks,spatial,title'),
            ('format', 'json'),
            ('parentId', self._parent_id)
        ]

        r = requests.get(base_url, params=params)
        features = pd.DataFrame(r.json()['items'])
        features = features.loc[~features.title.str.contains('Imperv')]
        features = features.loc[~features.title.str.contains('by State')]
        features = features.loc[~features.title.str.contains('Tree Canopy')]
        features['geometry'] = features['spatial'].apply(_bbox2poly)
        features['download_url'] = features.webLinks.apply(_parse_links)
        features['filename'] = features['download_url'].str.rsplit('/', n=1, expand=True)[1]
        features['reserved'] = features.apply(
            lambda x: {'download_url': x['download_url'],
                       'filename': x['filename'],
                       'file_format': 'raster-gdal',
                       'extract_from_zip': '.tif',
                       }, axis=1)

        features['parameters'] = 'landcover'
        features.rename(columns={'id': 'service_id', 'title': 'display_name'},
                        inplace=True)
        features.index = features['service_id']

        # remove extra fields. nested dicts can cause problems
        del features['relatedItems']
        del features['webLinks']
        del features['spatial']
        del features['link']
        del features['download_url']
        del features['filename']

        return features


class UsgsNlcdService2001(UsgsNlcdServiceBase):
    service_name = '2001'
    display_name = 'NLCD {} Land Cover'.format(service_name)
    description = 'Retrieve NLCD {}'.format(service_name)
    _parent_id = '4f70a45ee4b058caae3f8db9'


class UsgsNlcdService2006(UsgsNlcdServiceBase):
    service_name = '2006'
    display_name = 'NLCD {} Land Cover'.format(service_name)
    description = 'Retrieve NLCD {}'.format(service_name)
    _parent_id = '4f70a46ae4b058caae3f8dbb'


class UsgsNlcdService2011(UsgsNlcdServiceBase):
    service_name = '2011'
    display_name = 'NLCD {} Land Cover'.format(service_name)
    description = 'Retrieve NLCD {}'.format(service_name)
    _parent_id = '513624bae4b03b8ec4025c4d'


class UsgsNlcdProvider(ProviderBase):
    service_list = [UsgsNlcdService2001, UsgsNlcdService2006, UsgsNlcdService2011]
    display_name = 'National Land Cover Database'
    description = 'The National Land Cover Database products are created through a cooperative project conducted by ' \
                  'the Multi-Resolution Land Characteristics (MRLC) Consortium. The MRLC Consortium is a partnership ' \
                  'of federal agencies (www.mrlc.gov), consisting of ' \
                  'the U.S. Geological Survey (USGS), ' \
                  'the National Oceanic and Atmospheric Administration (NOAA), ' \
                  'the U.S. Environmental Protection Agency (EPA), ' \
                  'the U.S. Department of Agriculture -Forest Service (USDA-FS), ' \
                  'the National Park Service (NPS), ' \
                  'the U.S. Fish and Wildlife Service (FWS), ' \
                  'the Bureau of Land Management (BLM), and ' \
                  'the USDA Natural Resources Conservation Service (NRCS).'
    organization_name = 'United States Geological Survey'
    organization_abbr = 'USGS'
    name = 'usgs-nlcd'


def _bbox2poly(bbox):
    xmin = bbox['boundingBox']['minX']
    xmax = bbox['boundingBox']['maxX']
    ymin = bbox['boundingBox']['minY']
    ymax = bbox['boundingBox']['maxY']

    return util.bbox2poly(xmin, ymin, xmax, ymax, as_shapely=True)


def _parse_links(links):
    return [link['uri'] for link in links if link['type'] == 'download'][0]
