from .base import ProviderBase, SingleFileServiceBase, PublishBase
from ..api.database import get_db, db_session
from shapely.geometry import Point, box
from ..api.metadata import get_metadata
from ..util import param_util
from getpass import getpass
import girder_client
import pandas as pd
import param


class GirderServiceBase(SingleFileServiceBase):

    @property
    def gc(self):
        return self.provider.get_gc()

    def get_features(self, **kwargs):
        raise NotImplementedError()


class GirderGeoService(GirderServiceBase):
    service_name = 'girder_geo'
    display_name = 'Girder Geo Service'
    description = 'Girder is a repository for ERDC ERS.'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {}

    # def get_features(self, **kwargs):
    #
    #     results = list(self.hs.resources())
    #
    #     if len(results) == 0:
    #         raise ValueError('No resource available from Data Depot.')
    #
    #     results2 = [item for item in results if len(item['coverages']) != 0]
    #
    #     if len(results2) == 0:
    #         raise ValueError("There is no resources with coverages in Data Depot Repository.")
    #
    #
    #     features = pd.DataFrame(results2)
    #     idx = features['coverages'].apply(lambda x: len([c for c in x if c['type'] != 'period']) > 0)
    #     features = features[idx]
    #
    #     features['geometry'] = features['coverages'].apply(self.parse_coverages)
    #     features['service_id'] = features['resource_id'].apply(str)
    #     features.index = features['service_id']
    #     features.rename(columns={
    #         'resource_title': 'display_name',
    #         'bag_url': 'download url'
    #     }, inplace=True)
    #     features['filename'] = features['download url'].apply(lambda x: x.split('/')[-1])
    #     features['reserved'] = features.apply(
    #         lambda x: {'download_url': x['download url'],
    #                    'filename': x['filename'],
    #                    'file_format': 'zip',
    #                    }, axis=1)
    #
    #     return features
    #
    # def parse_coverages(self, resource_row):
    #     geometry = None
    #     for coverage in resource_row:
    #         coverage_type = coverage.get('type')
    #         if coverage_type == 'point':
    #             geometry = Point(float(coverage.get('value').get('north')), float(coverage.get('value').get('east')))
    #         elif coverage_type == 'box':
    #             geometry = box(float(coverage.get('value').get('westlimit')),
    #                            float(coverage.get('value').get('southlimit')),
    #                            float(coverage.get('value').get('eastlimit')),
    #                            float(coverage.get('value').get('northlimit')))
    #
    #     return geometry


class GirderNormService(GirderServiceBase):
    service_name = "girder_norm"
    display_name = "Girder Normal Service"
    description = 'Girder is a repository for ERDC ERS.'
    service_type = "norm-discrete"
    unmapped_parameters_available = True
    _parameter_map = {}

    # def get_features(self, **kwargs):
        # results = list(self.gc.listCollection())
        # features = pd.DataFrame(results)
        # features['service_id'] = features['_id'].apply(str)
        # features.index = features['service_id']
        # features.rename(columns={'resource_title': 'name', 'bag_url': 'download url'}, inplace=True)
        # features['filename'] = features['download url'].apply(lambda x: x.split('/')[-1])
        # features['reserved'] = features.apply(
        #     lambda x: {'download_url': x['download url'],
        #                'filename': x['filename'],
        #                'file_format': 'zip',
        #                }, axis=1)
        #
        # return features


class GirderPublisher(PublishBase):
    publisher_name = "girder_pub"
    display_name = "Girder Publisher"
    description = "Girder is a preository for ERDC ERS."

    title = param.String(default="example title", doc="Title of resource", precedence=1)
    collection_description = param.String(default="No descritpion avaliable.", doc="Description of resource", precedence=2)
    folder_name = param.String(default="example folder title", doc="Folder Title", precedence=3)
    folder_description = param.String(default="No descritpion avaliable.", doc="Folder Description", precedence=4)
    # Have the option to make the resource public.
    dataset = param_util.DatasetListSelector(default=(), filters={'status': 'downloaded'}, precedence=5, doc="dataset to publish to HydroShare")

    def __init__(self, provider, **kwargs):
        super(GirderPublisher, self).__init__(provider, **kwargs)

    @property
    def gc(self):
        return self.provider.get_gc()

    def publish(self, options=None):
        try:
            p = param.ParamOverrides(self, options)
            params = {'name': p.name, 'description': p.description}
            resource_information_dict = self.gc.createResource(path='collection', params=params)
            folder_creation_dict = self.gc.createFolder(parentId=resource_information_dict['_id'], name=p.folder_name, description=p.folder_description, parentType='collection')
            for dataset in p.dataset:
                dataset_metadata = get_metadata(dataset)[dataset]
                fpath = dataset_metadata['file_path']
                self.gc.uploadFileToFolder(folder_creation_dict['_id'], fpath)
        except Exception as e:
            raise e

        return resource_information_dict['_id']


class GirderProvider(ProviderBase):
    service_base_class = GirderServiceBase
    publishers_list = [GirderPublisher]
    display_name = 'Girder Services'
    description = 'Services avaliable through the AFRL Girder Server.'
    organization_name = 'U.S. Air Force Research Laboratory'
    organization_abbr = 'AFRL'

    def get_gc(self):
        connection_info = 'https://data.kitware.com/api/v1'

        try:
            gc = girder_client.GirderClient(connection_info)
            gc.authenticate(**self.credentials)
            return gc
        except:
            try:
                gc = girder_client.GirderClient(connection_info)
            except:
                raise ValueError("Cannot connect to the Girder.")

        return gc

    def authenticate_me(self, **kwargs):
        connection_info = 'https://data.kitware.com/api/v1'
        username = input("Enter Username: ")
        password = getpass("Enter Password: ")

        try:
            gc = girder_client.GirderClient(connection_info)
            gc.authenticate(username, password)
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
            print("Either credentials invalid or unable to connect to the Girder live server.")

        return False