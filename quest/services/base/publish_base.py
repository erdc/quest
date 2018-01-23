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


class PublishBase():
    """Base class for data publish plugins
    """
    # service_base_class = None
    # display_name = None
    # description = None
    # organization_name = None
    # organization_abbr = None

    # @property
    # def services(self):
    #     pass
    #
    # @property
    # def metadata(self):
    #     pass

    def __init__(self):
        pass

    def get_features(self, service, update_cache=False, **kwargs):
        pass

    def _label_features(self, features, service):
        pass

    def get_tags(self, service, update_cache=False):
        pass

    def _get_tags_from_dict(self, tag, d):
        pass

    def _combine_dicts(self, this, other):
        pass

    def get_services(self):
        pass

    def get_parameters(self, service, features=None):
        pass

    def download(self, service, feature, file_path, dataset, **kwargs):
        pass

    def download_options(self, service, fmt):
        pass


