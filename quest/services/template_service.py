# standard python library imports
import os

# third party library imports
import pandas as pd
import param

# Quest imports
from .base import ProviderBase, ServiceBase
from .. import util


class ExampleServiceBase(ServiceBase):
    """

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
    smtk_template = None
    _parameter_map = dict()

    def download(self, feature, file_path, dataset, **params):
        metadata = {}  # get metadata from service
        data = None  # data structure containing downloaded data

        quest_metadata = {
            'metadata': metadata,
            'file_path': file_path,
            'file_format': '',
            'datatype': '',
            'parameter': '',
            'unit': '',
            'service_id': util.construct_service_uri(self.service_name, feature)
        }

        # save data to disk
        io_driver_type = ''  # name of the io driver to save data type
        # io = util.load_drivers('io', io_driver_type)[io_driver_type].driver
        # io.write(file_path, data, quest_metadata)
        del quest_metadata['service_id']

        return quest_metadata

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
        return pd.DataFrame()


class ExampleService1(ExampleServiceBase):
    service_name = 'example-1'
    display_name = None
    description = None
    service_type = None
    unmapped_parameters_available = None
    geom_type = None
    datatype = None
    geographical_areas = None
    bounding_boxes = None
    smtk_template = None
    _parameter_map = {}


class ExampleService2(ExampleServiceBase):
    service_name = 'example-2'
    display_name = None
    description = None
    service_type = None
    unmapped_parameters_available = None
    geom_type = None
    datatype = None
    geographical_areas = None
    bounding_boxes = None
    smtk_template = None
    _parameter_map = {}


class ExampleProvider(ProviderBase):
    service_base_class = ExampleServiceBase
    display_name = 'Example Web Provider'
    description = 'Example ProviderBase subclass for Quest'
    organization_name = 'Example Data Provider Organization'
    organization_abbr = 'EDPO'