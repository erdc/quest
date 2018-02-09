from .base import ProviderBase, SingleFileServiceBase, PublishBase
from hs_restclient import HydroShare, HydroShareAuthBasic
from shapely.geometry import Point, box
import pandas as pd
from getpass import getpass
from ..api.database import get_db, db_session


class HSServiceBase(SingleFileServiceBase):

    def get_features(self, **kwargs):

        try:
            auth = self.provider.auth
            self.hs = HydroShare(auth=auth)
        except:
            self.hs = HydroShare()

        results = list(self.hs.resources())

        features = pd.DataFrame(results)
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
                geometry = box(float(coverage.get('value').get('westlimit')), float(coverage.get('value').get('southlimit')), float(coverage.get('value').get('eastlimit')), float(coverage.get('value').get('northlimit')))
        return geometry

    def _get_parameters(self, features=None):
        pass


class HSGeoService(HSServiceBase):
    service_name = 'hs_geo'
    display_name = 'HydroShare Geo Service'
    description = 'Center for Operational Oceanographic Products and Services'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {}


class HSPublisher(PublishBase):
    publisher_name = "hs_normal"
    display_name = "HydroShare Publisher"
    description = "empty"

    def __init__(self, provider, **kwargs):
        super(HSPublisher, self).__init__(provider, **kwargs)

    def publish(self):

        try:
            auth = self.provider.auth
        except:
            raise ValueError('Provider does not exist in the database.')

        self.hs = HydroShare(auth=auth)
        abstract = 'My latex abstract'
        title = 'My latex resource'
        keywords = ('Latex', 'examples')
        rtype = 'GenericResource'
        fpath = '/Users/rditlaav/Documents/service.py'
        metadata = '[{"coverage":{"type":"period", "value":{"start":"01/01/2000", "end":"12/12/2010"}}}, {"creator":{"name":"John Smith"}}, {"creator":{"name":"Lisa Miller"}}]'
        resource_id = self.hs.createResource(rtype, title, resource_file=fpath, keywords=keywords, abstract=abstract, metadata=metadata)
        print("Resource ID: ", resource_id)


class HSProvider(ProviderBase):
    service_base_class = HSServiceBase
    publishers_list = [HSPublisher]
    display_name = 'Hydro Web Services'
    description = 'Services avaliable through the ERDC HydroSHare Server.'
    organization_name = 'U.S. Army Engineering Research and Development Center'
    organization_abbr = 'ERDC'

    @property
    def auth(self):
        return HydroShareAuthBasic(**self.credentials)


    def authenticate_me(self, **kwargs):

        username = getpass("Enter Username: ")
        password = getpass("Enter Password: ")

        try:
            self._auth = HydroShareAuthBasic(username=username, password=password)
            hs = HydroShare(auth=self.auth)
            hs.resources(count=1)
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
            print("Credentials were invalid.")

        return False