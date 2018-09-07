from quest import util
import os
import ulmo
from quest.util.log import logger
from quest.util.param_util import format_json_options
import param


# base class for providers
# TODO can I make this an abc and have it be a Paramitarized?
class ServiceBase(param.Parameterized):
    """Base class for data providers
    """
    service_name = None
    display_name = None
    description = None
    service_type = None
    unmapped_parameters_available = None
    geom_type = None
    datatype = None
    geographical_areas = None
    bounding_boxes = None
    _parameter_map = None

    # name = param.String(default='Service', precedence=-1)

    def __init__(self, provider, **kwargs):
        self.provider = provider
        super(ServiceBase, self).__init__(**kwargs)

    @property
    def title(self):
        return '{} Download Options'.format(self.display_name)

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
        if hasattr(self, 'parameter'):
            pmap = self.parameter_map(invert=True)
            return pmap[self.parameter]

    def parameter_map(self, invert=False):
        pmap = self._parameter_map

        if pmap is None:
            raise NotImplementedError()

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def get_parameters(self, features=None):
        """Default function that should be overridden if the features argument needs to be handled."""
        return self.parameters

    def get_download_options(self, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

        if fmt == 'param':
            schema = self

        elif fmt == 'json':
            schema = format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema

    def download(self, feature, file_path, dataset, **kwargs):
        raise NotImplementedError()

    def get_features(self, **kwargs):
        """
        should return a pandas dataframe or a python dictionary with
        indexed by feature uid and containing the following columns

        reserved column/field names
            display_name -> will be set to uid if not provided
            description -> will be set to '' if not provided
            download_url -> optional download url

            defining geometry options:
                1) geometry -> geojson string or shapely object
                2) latitude & longitude columns/fields
                3) geometry_type, latitudes, longitudes columns/fields
                4) bbox column/field -> tuple with order (lon min, lat min, lon max, lat max)

        all other columns/fields will be accumulated in a dict and placed
        in a metadata field.
        :param **kwargs:

        """
        raise NotImplementedError()


class TimePeriodServiceBase(ServiceBase):
    start = param.Date(default=None, precedence=2, doc='start date')
    end = param.Date(default=None, precedence=3, doc='end date')

    @property
    def start_string(self):
        return self.start.strftime('%Y-%m-%d')

    @property
    def end_string(self):
        return self.end.strftime('%Y-%m-%d')


# abc
class SingleFileServiceBase(ServiceBase):
    """Base file for datasets that are a single file download
    eg elevation raster etc
    """
    def download(self, feature, file_path, dataset, **kwargs):
        feature_id = util.construct_service_uri(self.provider.name, self.name, feature)
        feature = self.provider.get_features(self.name).loc[feature_id]
        reserved = feature.get('reserved')
        download_url = reserved['download_url']
        fmt = reserved.get('extract_from_zip', '')
        filename = reserved.get('filename', util.uuid('dataset'))
        file_path = self._download_file(file_path, download_url, fmt, filename)
        return {
            'file_path': file_path,
            'file_format': reserved.get('file_format'),
            'parameter': feature.get('parameters'),
            'datatype': self.datatype,
        }

    def _download_file(self, path, url, tile_fmt, filename, check_modified=False):
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, 'zip'), exist_ok=True)
        tile_path = os.path.join(path, filename)
        logger.info('... downloading %s' % url)

        if tile_fmt == '':
            ulmo.util.download_if_new(url, tile_path, check_modified=check_modified)
        else:
            zip_path = os.path.join(path, 'zip', filename)
            ulmo.util.download_if_new(url, zip_path, check_modified=check_modified)
            logger.info('... ... zipfile saved at %s' % zip_path)
            tile_path = ulmo.util.extract_from_zip(zip_path, tile_path, tile_fmt)

        return tile_path