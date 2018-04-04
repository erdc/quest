from .base import ProviderBase, SingleFileServiceBase, PublishBase
from ..api.database import get_db, db_session
from shapely.geometry import Point, box
from ..api.metadata import get_metadata
from ..util import param_util
from getpass import getpass
import girder_client
import pandas as pd
import param
import os


class ISEPServiceBase(SingleFileServiceBase):

    token = param.String(default=None, doc="Token #", precedence=1)

    @property
    def gc(self):
        return self.provider.get_gc()

    def get_features(self, **kwargs):
        raise NotImplementedError()


class ISEPPublisher(PublishBase):
    publisher_name = "girder_pub"
    display_name = "Girder Publisher"
    description = "Girder is a repository for ERDC ERS."

    token = param.String(default=None, doc="Token #", precedence=1)
    title = param.String(default="example title", doc="Title of resource", precedence=2)
    collection_description = param.String(default="", doc="Description of resource", precedence=3)
    folder_name = param.String(default="example folder title", doc="Folder Title", precedence=4)
    folder_description = param.String(default="", doc="Folder Description", precedence=5)
    # Have the option to make the resource public.
    dataset = param_util.DatasetListSelector(default=(),
                                             filters={'status': 'downloaded'},
                                             precedence=6,
                                             doc="dataset to publish to HydroShare")

    def __init__(self, provider, **kwargs):
        super(ISEPPublisher, self).__init__(provider, **kwargs)

    @property
    def gc(self):
        return self.provider.get_gc()

    def publish(self, options=None):
        try:
            with self.gc.session() as session:
                p = param.ParamOverrides(self, options)
                session.verify = '/home/valoroso/DoD_Cert.pem'
                self.gc.token = p.token
                params = {'name': p.title, 'description': p.collection_description}
                resource_information_dict = self.gc.createResource(path='collection', params=params)
                folder_creation_dict = self.gc.createFolder(parentId=resource_information_dict['_id'],
                                                            name=p.folder_name,
                                                            description=p.folder_description,
                                                            parentType='collection')
                for dataset in p.dataset:
                    dataset_metadata = get_metadata(dataset)[dataset]
                    fpath = dataset_metadata['file_path']
                    self.gc.uploadFileToFolder(folder_creation_dict['_id'], fpath)

        except Exception as e:
            raise e

        return resource_information_dict['_id']


class GirderProvider(ProviderBase):
    service_base_class = ISEPServiceBase
    publishers_list = [ISEPPublisher]
    display_name = 'Girder Services'
    description = 'Services avaliable through the AFRL Girder Server.'
    organization_name = 'U.S. Air Force Research Laboratory'
    organization_abbr = 'AFRL'

    def get_gc(self):
        connection_info = 'https://talonw4.afrl.hpc.mil/api/v1'
        try:
            gc = girder_client.GirderClient(apiUrl=connection_info)
        except:
            raise ValueError("Cannot connect to the ISEP Girder.")

        return gc

    def authenticate_me(self, **kwargs):
        pass

