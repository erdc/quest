import param
import girder_client

from quest.util import param_util, log
from quest.api.metadata import get_metadata
from quest.plugins import ProviderBase, PublishBase
from quest.database.database import get_db, db_session

# There is no service base fore the Live Girder Server due to the general layout of how
# the folders and files are layed out. It would be super difficult to look through
# everyone's collections and try to understand what data is in what collection.

# The Girder Publisher is very simple and basic. With Girder having no strict requirements
# of the hiearchy, I just create one collection, one folder and put however many files that
# the user wants to put into it.


class GirderPublisher(PublishBase):
    publisher_name = "girder_pub"
    display_name = "Girder Publisher"
    description = "This is a Girder plugin for the live server."

    title = param.String(default="example title", doc="Title of resource", precedence=1)
    collection_description = param.String(default="", doc="Description of resource", precedence=2)
    folder_name = param.String(default="example folder title", doc="Folder Title", precedence=3)
    folder_description = param.String(default="", doc="Folder Description", precedence=4)
    # Have the option to make the resource public.
    dataset = param_util.DatasetListSelector(default=(),
                                             queries=['status == "downloaded" or status == "filter applied"'],
                                             precedence=5,
                                             doc="Dataset to publish to Girder")

    @property
    def gc(self):
        return self.provider.get_gc()

    def publish(self, **kwargs):
        try:
            p = param.ParamOverrides(self, kwargs)
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
    service_list = None
    publisher_list = [GirderPublisher]
    display_name = 'Girder Services'
    description = 'Services avaliable through the Live Girder Server.'
    organization_name = 'Kitware'
    name = 'kitware-girder'

    def get_gc(self):
        connection_info = 'https://data.kitware.com/api/v1'

        try:
            gc = girder_client.GirderClient(apiUrl=connection_info)
            gc.authenticate(**self.credentials)
            return gc
        except:
            try:
                gc = girder_client.GirderClient(apiUrl=connection_info)
            except:
                raise ValueError("Cannot connect to the Girder.")

        return gc

    def authenticate_me(self, **kwargs):
        connection_info = 'https://data.kitware.com/api/v1'
        username = kwargs['username']
        password = kwargs['password']

        try:
            gc = girder_client.GirderClient(apiUrl=connection_info)
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
            log.error("Either credentials invalid or unable to connect to the Girder live server.")

        return False
