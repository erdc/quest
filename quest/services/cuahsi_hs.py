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

class HSServiceBase(SingleFileServiceBase):

    @property
    def hs(self):
        return self.provider.get_hs()

    def get_features(self, **kwargs):
        raise NotImplementedError()


class HSGeoService(HSServiceBase):
    service_name = 'hs_geo'
    display_name = 'HydroShare Geo Service'
    description = 'HydroShare is a cuahsi repository fpr geo-discrete resources.'
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
            raise ValueError('No resource available from HydroShare.')

        results2 = [item for item in results if len(item['coverages']) != 0]

        if len(results2) == 0:
            raise ValueError("There is no resources with coverages in HydroShare Repository.")


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


class HSNormService(HSServiceBase):
    service_name = "hs_norm"
    display_name = "HydroShare Normal Service"
    description = 'HydroShare is a cuahsi repository for all recource types.'
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


class HSPublisher(PublishBase):
    publisher_name = "hs_pub"
    display_name = "HydroShare Publisher"
    description = "HydroShare is a cuahsi repository for all resource types"

    _resource_type_map = {
        'Composite': 'CompositeResource',
        'Generic': 'GenericResource',
        'Geographic Feature': 'GeographicFeatureResource',
        'Geographic Raster': 'RasterResource',
        'MODFLOW Model Instance': 'MODFLOWModelInstanceResource',
        'Model Instance': 'ModelInstanceResource',
        'Model Program': 'ModelProgramResource',
        'Multidimentionsal (NetCDF)': 'NetcdfResource',
        'SWAT Model Instance': 'SWATModelInstanceResource',
        'Script': 'ScriptResource',
        'Time Series': 'TimeSeriesResource'
    }

    title = param.String(default="example title", doc="Title of resource", precedence=2)
    abstract = param.String(default="example abstract", precedence=3,
                            doc="An description of the resource to be added to HydroShare.")
    keywords = param.List(default=[], precedence=4, doc="list of keyword strings to describe the resource")
    dataset = param_util.DatasetListSelector(default=(), filters={'status': 'downloaded'}, precedence=5,
                                             doc="dataset to publish to HydroShare")
    resource_type = param.ObjectSelector(doc='parameter', precedence=1, objects=sorted(_resource_type_map.keys()))

    def __init__(self, provider, **kwargs):
        super(HSPublisher, self).__init__(provider, **kwargs)

    @property
    def hs(self):
        return self.provider.get_hs()

    def publish(self, options=None):

        p = param.ParamOverrides(self, options)
        valid_file_paths = []
        valid_extensions = []

        if p.resource_type == "":
            raise ValueError("There was no resource type selected.")
        else:
            resource_type = self._resource_type_map[p.resource_type]

        extension_dict = {
            'GeographicFeatureResource': ['.zip', '.shp', '.shx', '.dbf', '.prj', '.sbx', '.sbn', '.cpg', '.xml',
                                          '.fbn', '.fbx', '.ain', '.alh', '.atx', '.ixs', '.mxs'],
            'RasterResource': ['.zip', '.tif'],
            'NetcdfResource': ['.nc'],
            'ScriptResource': ['.r', '.py', '.m'],
            'TimeSeriesResource': ['.sqlite', '.csv']}

        if resource_type in ['GeographicFeatureResource', 'RasterResource', 'NetcdfResource', 'ScriptResource',
                             'TimeSeriesResource']:
            valid_extensions = extension_dict[resource_type]

        if len(p.dataset) > 1 and resource_type in ['TimeSeriesResource', 'RasterResource']:
            raise ValueError("The selected resource cannot have more than one dataset.")

        if len(p.dataset) == 0:
            raise ValueError("There was no dataset selected.")

        for dataset in p.dataset:
            dataset_metadata = get_metadata(dataset)[dataset]
            fpath = dataset_metadata['file_path']
            filename, file_extension = os.path.splitext(fpath)

            if len(valid_extensions) != 0:
                if file_extension in valid_extensions:
                    valid_file_paths.append(fpath)
                else:
                    raise ValueError("There was a problem with one of the dataset file extentions for your resource.")
            else:
                valid_file_paths.append(fpath)

        resource_id = self.create_resource(resource_type=resource_type, title=p.title,
                                           file_path=valid_file_paths[0], keywords=p.keywords, abstract=p.abstract)

        for path in valid_file_paths[1:]:
            self.add_file_to_resource(resource_id, path)

        return resource_id

    def create_resource(self, title=None, abstract=None, keywords=None, resource_type=None, file_path="",
                        metadata=None, extra_metadata=None):

        try:
            resource_id = self.hs.createResource(resource_type, title, resource_file=file_path, keywords=keywords,
                                                 abstract=abstract, metadata=metadata,
                                                 extra_metadata=extra_metadata)
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


class HSProvider(ProviderBase):
    service_base_class = HSServiceBase
    publishers_list = [HSPublisher]
    display_name = 'HydroShare Services'
    description = 'Services avaliable through the live HydroShare Server.'
    organization_name = 'Cuahsi'

    @property
    def auth(self):
        return HydroShareAuthBasic(**self.credentials)

    def get_hs(self, auth=None, require_valid_auth=False):
        try:
            auth = auth or self.auth
            hs = HydroShare(auth=auth)
            list(hs.resources(count=1))
            return hs
        except Exception as e:
            if require_valid_auth:
                raise e

        try:
            hs = HydroShare()
            list(hs.resources(count=1))
        except:
            raise ValueError("Cannot connect to the  HydroShare.")

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

        except:
            print("Either credentials invalid or unable to connect to HydroShare.")

        return False

