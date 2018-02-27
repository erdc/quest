from .base import ProviderBase, SingleFileServiceBase, PublishBase
from hs_restclient import HydroShare, HydroShareAuthBasic
from shapely.geometry import Point, box
import pandas as pd
from getpass import getpass
from ..api.database import get_db, db_session
from ..api.metadata import get_metadata
import param
from ..util import param_util


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
    publisher_name = "dd_normal"
    display_name = "Data Depot Publisher"
    description = "empty"

    title = param.String(default="example title", doc="Title of resource", precedence=1)
    abstract = param.String(default="example abstract",  precedence=2, doc="An description of the resource to be added to HydroShare.")
    keywords = param.List(precedence=3, doc="list of keyword strings to describe the resource")
    dataset = param_util.DatasetSelector(filters={'status': 'downloaded'}, precedence=4, doc="dataset to publish to HydroShare")

    def __init__(self, provider, **kwargs):
        super(DDPublisher, self).__init__(provider, **kwargs)

    @property
    def hs(self):
        return self.provider.get_hs()

    def publish(self, options=None):

        p = param.ParamOverrides(self, options)
        rtype = 'GenericResource'
        dataset_metadata = get_metadata(p.dataset)[p.dataset]
        fpath = dataset_metadata['file_path']
        metadata = dataset_metadata['metadata']
        resource_id = self.hs.createResource(rtype, p.title, resource_file=fpath, keywords=p.keywords, abstract=p.abstract, metadata=metadata)

        return resource_id


class DDProvider(ProviderBase):
    service_base_class = DDServiceBase
    publishers_list = [DDPublisher]
    display_name = 'Data Depot Services'
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