import requests
import pandas as pd

from quest import util
from quest.static import ServiceType, DatasetSource
from quest.plugins import ProviderBase, SingleFileServiceBase


class UsgsNlcdServiceBase(SingleFileServiceBase):
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = False
    geom_type = 'polygon'
    datatype = 'discrete-raster'
    geographical_areas = ['USA']
    bounding_boxes = [[-130.232828, 21.742308, -63.672192, 52.877264]]
    _parameter_map = {
        'landcover': 'landcover'
    }

    def search_catalog(self, **kwargs):
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
        catalog_entries = pd.DataFrame(r.json()['items'])
        catalog_entries = catalog_entries.loc[~catalog_entries.title.str.contains('Imperv')]
        catalog_entries = catalog_entries.loc[~catalog_entries.title.str.contains('by State')]
        catalog_entries = catalog_entries.loc[~catalog_entries.title.str.contains('Tree Canopy')]
        catalog_entries['geometry'] = catalog_entries['spatial'].apply(_bbox2poly)
        catalog_entries['download_url'] = catalog_entries.webLinks.apply(_parse_links)
        catalog_entries['filename'] = catalog_entries['download_url'].str.rsplit('/', n=1, expand=True)[1]
        catalog_entries['reserved'] = catalog_entries.apply(
            lambda x: {'download_url': x['download_url'],
                       'filename': x['filename'],
                       'file_format': 'raster-gdal',
                       'extract_from_zip': '.tif',
                       }, axis=1)

        catalog_entries['parameters'] = 'landcover'
        catalog_entries.rename(columns={'id': 'service_id', 'title': 'display_name'},
                        inplace=True)
        catalog_entries.index = catalog_entries['service_id']

        # remove extra fields. nested dicts can cause problems
        del catalog_entries['relatedItems']
        del catalog_entries['webLinks']
        del catalog_entries['spatial']
        del catalog_entries['link']
        del catalog_entries['download_url']
        del catalog_entries['filename']

        return catalog_entries


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
                  'the Multi-Resolution Land Characteristics (MRLC) Consortium.'
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
