from .base import ProviderBase, SingleFileServiceBase, PublishBase
from hs_restclient import HydroShare, HydroShareAuthBasic
from ..api.database import get_db, db_session
from shapely.geometry import Point, box
from ..api.metadata import get_metadata
from ..util import param_util
from getpass import getpass
import pandas as pd
import param
import os

class DDServiceBase(SingleFileServiceBase):

    @property
    def hs(self):
        return self.provider.get_hs()

    def get_features(self, **kwargs):
        raise NotImplementedError()


class DDGeoService(DDServiceBase):
    service_name = 'dd_geo'
    display_name = 'Data Depot Geo Service'
    description = 'Data Depot is a repository for ERDC ERS.'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {}

    def get_features(self, **kwargs):

        results = list(self.hs.resources())

        if len(results) == 0:
            raise ValueError('No resource available from Data Depot.')

        results2 = [item for item in results if len(item['coverages']) != 0]

        if len(results2) == 0:
            raise ValueError("There is no resources with coverages in Data Depot Repository.")


        features = pd.DataFrame(results2)
        idx = features['coverages'].apply(lambda x: len([c for c in x if c['type'] != 'period']) > 0)
        features = features[idx]

        features['geometry'] = features['coverages'].apply(self.parse_coverages)
        features['service_id'] = features['resource_id'].apply(str)
        features.index = features['service_id']
        features.rename(columns={
            'resource_title': 'display_name',
            'bag_url': 'download url'
        }, inplace=True)
        features['filename'] = features['download url'].apply(lambda x: x.split('/')[-1])
        features['reserved'] = features.apply(
            lambda x: {'download_url': x['download url'],
                       'filename': x['filename'],
                       'file_format': 'zip',
                       }, axis=1)

        return features

    def parse_coverages(self, resource_row):
        geometry = None
        for coverage in resource_row:
            coverage_type = coverage.get('type')
            if coverage_type == 'point':
                geometry = Point(float(coverage.get('value').get('north')), float(coverage.get('value').get('east')))
            elif coverage_type == 'box':
                geometry = box(float(coverage.get('value').get('westlimit')),
                               float(coverage.get('value').get('southlimit')),
                               float(coverage.get('value').get('eastlimit')),
                               float(coverage.get('value').get('northlimit')))

        return geometry


class DDNormService(DDServiceBase):
    service_name = "dd_norm"
    display_name = "Data Depot Normal Service"
    description = 'Data Depot is a repository for ERDC ERS.'
    service_type = "norm-discrete"
    unmapped_parameters_available = True
    _parameter_map = {}

    def get_features(self, **kwargs):
        results = list(self.hs.resources())
        features = pd.DataFrame(results)
        features['service_id'] = features['resource_id'].apply(str)
        features.index = features['service_id']
        features.rename(columns={
            'resource_title': 'display_name',
            'bag_url': 'download url'
        }, inplace=True)
        features['filename'] = features['download url'].apply(lambda x: x.split('/')[-1])
        features['reserved'] = features.apply(
            lambda x: {'download_url': x['download url'],
                       'filename': x['filename'],
                       'file_format': 'zip',
                       }, axis=1)

        return features


class DDPublisher(PublishBase):
    publisher_name = "dd_pub"
    display_name = "Data Depot Publisher"
    description = "empty"

    _parameter_map = {
        'CompositeResource': 'Composite',
        'GenericResource': 'Generic',
        'GeographicFeatureResource': 'Geographic Feature',
        'RasterResource': 'Geographic Raster',
        'ModelInstanceResource': 'Model Instance',
        'ModelProgramResource': 'Model Program',
        'MODFLOWModelInstanceResource': 'MODFLOW Model Instance',
        'NetcdfResource': 'Multidimentionsal (NetCDF)',
        'ScriptResource': 'Script',
        'SWATModelInstanceResource': 'SWAT Model Instance',
        'TimeSeriesResource': 'Time Series',
        }

    title = param.String(default="example title", doc="Title of resource", precedence=1)
    abstract = param.String(default="example abstract",  precedence=2, doc="An description of the resource to be added to HydroShare.")
    keywords = param.List(default=[], precedence=3, doc="list of keyword strings to describe the resource")
    dataset = param_util.DatasetListSelector(default=(), filters={'status': 'downloaded'}, precedence=4, doc="dataset to publish to HydroShare")
    resource_type = param.ObjectSelector(default="", doc='parameter', precedence=1, objects=sorted(_parameter_map.values()))

    def __init__(self, provider, **kwargs):
        super(DDPublisher, self).__init__(provider, **kwargs)

    @property
    def hs(self):
        return self.provider.get_hs()

    def publish(self, options=None):
        resource_id = None
        p = param.ParamOverrides(self, options)

        if p.resource_type == "":
            raise ValueError("There was no resource type selected.")

        if len(p.dataset) == 1:
            dataset_metadata = get_metadata(p.dataset)[p.dataset]
            metadata = dataset_metadata['metadata']
            fpath = dataset_metadata['file_path']
            filename, file_extension = os.path.splitext(fpath)

            if p.resource_type == 'GeographicFeatureResource':
                geo_feature_list = ['.zip', '.shp', '.shx', '.dbf', '.prj', '.sbx', '.sbn', '.cpg', '.xml', '.fbn', '.fbx', '.ain', '.alh', '.atx', '.ixs', '.mxs']
                if file_extension not in geo_feature_list:
                    raise ValueError("Dataset file is not supported in the Geographic Feature Resource Type.")
            elif p.resource_type == 'RasterResource':
                if file_extension != '.tif' or file_extension != '.zip':
                    raise ValueError("Dataset file is not supported in the Geographic Raster Resource Type.")
            elif p.resource_type == 'NetcdfResource':
                if file_extension != '.nc':
                    raise ValueError("Dataset file is not supported in the Multidimensional (NetCDF) Resource Type.")
            elif p.resource_type == 'ScriptResource':
                if file_extension != '.r' or file_extension != '.py' or file_extension != '.m':
                    raise ValueError("Dataset file is not supported in the Script Resource Type.")
            elif p.resource_type == 'TimeSeriesResource':
                if file_extension != '.sqlite' or file_extension != '.csv':
                    raise ValueError("Dataset file is not supported in the Time Series Resource Type.")

            resource_id = self.create_resource(p.resource_type, p.title, resource_file=fpath, keywords=p.keywords, abstract=p.abstract, metadata=metadata)

        elif len(p.dataset) > 1:
            error_flag = None
            error_message = ""
            metadata = {}

            resource_id = self.create_resource(p.resource_type, p.title, keywords=p.keywords, abstract=p.abstract)

            for dataset in p.dataset:
                dataset_metadata = get_metadata(p.dataset)[p.dataset]
                metadata[dataset] = dataset_metadata['metadata']
                fpath = dataset_metadata['file_path']
                filename, file_extension = os.path.splitext(fpath)

                if p.resource_type == 'GeographicFeatureResource':
                    geo_feature_list = ['.zip', '.shp', '.shx', '.dbf', '.prj', '.sbx', '.sbn', '.cpg', '.xml', '.fbn', '.fbx', '.ain', '.alh', '.atx', '.ixs', '.mxs']
                    if file_extension not in geo_feature_list:
                        error_flag = True
                        error_message = "Dataset file is not supported in the Geographic Feature Resource Type."
                elif p.resource_type == 'RasterResource':
                    error_flag = True
                    error_message = "This resource type does not allow multiple files."
                elif p.resource_type == 'NetcdfResource':
                    if file_extension != '.nc':
                        error_flag = True
                        error_message = "Dataset file is not supported in the Multidimensional (NetCDF) Resource Type."
                elif p.resource_type == 'ScriptResource':
                    if file_extension != '.r' or file_extension != '.py' or file_extension != '.m':
                        error_flag = True
                        error_message = "Dataset file is not supported in the Script Resource Type."
                elif p.resource_type == 'TimeSeriesResource':
                    error_flag = True
                    error_message = "This resource type does not allow multiple files."

                if error_flag is True:
                    self.delete_resource(resource_id)
                    raise ValueError(error_message)
                else:
                    self.add_file_to_resource(resource_id, fpath)

            self.hs.updateScienceMetadata(resource_id, metadata=metadata)

        else:
            raise ValueError("There was no datasets selected.")

        return resource_id

    def create_resource(self, title=None, abstract=None, keywords=None, resource_type=None, file_path=None, metadata=None, extra_metadata=None):

        if os.path.isdir(file_path) is True:
            raise ValueError("The file path cannot be a directory.")

        try:
            resource_id = self.hs.createResource(resource_type, title, resource_file=file_path, keywords=keywords, abstract=abstract, metadata=metadata, extra_metadata=extra_metadata)
        except Exception as e:
            raise e

        return resource_id

    def delete_resource(self, resource_id):

        try:
            self.hs.deleteResource(resource_id)
        except Exception as e:
            raise e

        return

    def add_file_to_resource(self, resource_id, file_path):

        if os.path.isdir(file_path) is True:
            raise ValueError("The file path cannot be a directory.")

        try:
            resource_id = self.hs.addResourceFile(resource_id, file_path)
        except Exception as e:
            raise e

        return resource_id

    def delete_file_from_resource(self, resource_id=None, file_name=None):

        try:
            resource_id = self.hs.deleteResourceFile(resource_id, file_name)
        except Exception as e:
            raise e

        return resource_id


class DDProvider(ProviderBase):
    service_base_class = DDServiceBase
    publishers_list = [DDPublisher]
    display_name = 'HydroShare Services'
    description = 'Services avaliable through the ERDC Data Depot Server.'
    organization_name = 'U.S. Army Engineering Research and Development Center'
    organization_abbr = 'ERDC'

    @property
    def auth(self):
        return HydroShareAuthBasic(**self.credentials)

    def get_hs(self, auth=None, require_valid_auth=False):
        connection_info = {'hostname': '192.168.56.106',
                           'port': 8000,
                           'verify': False,
                           'use_https': False
                           }

        try:
            auth = auth or self.auth
            hs = HydroShare(auth=auth, **connection_info)
            list(hs.resources(count=1))
            return hs
        except Exception as e:
            if require_valid_auth:
                raise e

        try:
            hs = HydroShare(**connection_info)
            list(hs.resources(count=1))
        except:
            raise ValueError("Cannot connect to the Data Depot Share.")

        return hs

    def authenticate_me(self, **kwargs):

        username = input("Enter Username: ")
        password = getpass("Enter Password: ")

        try:
            auth = HydroShareAuthBasic(username=username, password=password)
            self.get_hs(auth=auth, require_valid_auth=True)
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

        except Exception as e:
            print("Either credentials invalid or unable to connect to Data Depot.")

        return False