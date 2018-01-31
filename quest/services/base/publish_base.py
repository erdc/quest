from builtins import object
import abc
from future.utils import with_metaclass
from quest import util
import os
import pickle
import ulmo
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point, shape
from quest.util.log import logger
from quest.util.param_util import format_json_options
import json
import param


class PublishBase(param.Parameterized):
    # service_name = None
    # display_name = None
    # description = None
    # service_type = None
    # unmapped_parameters_available = None
    # geom_type = None
    # datatype = None
    # geographical_areas = None
    # bounding_boxes = None
    # smtk_template = None
    # _parameter_map = None
    #
    # name = param.String(default='Service', precedence=-1)

    # def __init__(self, provider, **kwargs):
    #     self.provider = provider
    #     super(ServiceBase, self).__init__(**kwargs)

    @property
    def title(self):
        # return '{} Download Options'.format(self.display_name)
        pass

    @property
    def metadata(self):
        # return {
        #     'display_name': self.display_name,
        #     'description': self.description,
        #     'service_type': self.service_type,
        #     'parameters': list(self._parameter_map.values()),
        #     'unmapped_parameters_available': self.unmapped_parameters_available,
        #     'geom_type': self.geom_type,
        #     'datatype': self.datatype,
        #     'geographical_areas': self.geographical_areas,
        #     'bounding_boxes': self.bounding_boxes
        # }
        pass

    @property
    def parameters(self):
        # return {
        #     'parameters': list(self._parameter_map.values()),
        #     'parameter_codes': list(self._parameter_map.keys())
        # }
        pass

    @property
    def parameter_code(self):
        # if hasattr(self, 'parameter'):
        #     pmap = self.parameter_map(invert=True)
        #     return pmap[self.parameter]
        pass

    def parameter_map(self, invert=False):
        # pmap = self._parameter_map
        #
        # if pmap is None:
        #     raise NotImplementedError()
        #
        # if invert:
        #     pmap = {v: k for k, v in pmap.items()}
        #
        # return pmap
        pass

    def get_parameters(self, features=None):
        # """Default function that should be overridden if the features argument needs to be handled."""
        # return self.parameters
        pass

    def publish_options(self, fmt):
        # """
        # needs to return dictionary
        # eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        # """
        #
        # if fmt == 'param':
        #     schema = self
        #
        # elif fmt == 'smtk':
        #     if self.smtk_template is None:
        #         return ''
        #     parameters = sorted(self.parameters['parameters'])
        #     parameters = [(p.capitalize(), p) for p in parameters]
        #     schema = util.build_smtk('download_options',
        #                              self.smtk_template,
        #                              title=self.title,
        #                              parameters=parameters)
        #
        # elif fmt == 'json':
        #     schema = format_json_options(self)
        #
        # else:
        #     raise ValueError('{} is an unrecognized format.'.format(fmt))
        #
        # return schema
        pass

    def publish(self, feature, file_path, dataset, **params):
        # raise NotImplementedError()
        pass



