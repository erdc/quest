from .base import ProviderBase, ServiceBase, PublishBase
from ..api.metadata import get_metadata
from ..api.database import get_db, db_session
from shapely.geometry import shape
from ckanapi import RemoteCKAN
from ..util import param_util
from getpass import getpass
import pandas as pd
import datetime
import geojson
import param
import os


class CKANServiceBase(ServiceBase):

    @property
    def demo(self):
        return self.provider.get_demo()

    def get_features(self, **kwargs):
        raise NotImplementedError()

    def get_data(self, **kwargs):
        """
            How this works is by grabbing the first 1000 rows of datasets from the ckan application.
            The package_search() call will return a dictionary that holds the total number of datasets
            that is being returned. By default the CKAN application only returns a max of 1000 rows at
            a time. Once I grab the first amount of datasets, I check to see if the count is greater
            than 1000, and if so I set a counter to 1001. I do this because if I got from 0 - 1000,
            then I want to grab from 1001 to 2001 and so on. I save the results to a list, then proceed
            to loop. I then grab the next group of datasets, increment my counter, and then add it to
            the list of other datasets.
        """
        results = self.demo.action.package_search(**kwargs, start=0, rows=1000)

        list_of_datasets = results['results']
        if results['count'] > 1000:
            counter = 1000
            total_datasets = results['count']
            while counter < total_datasets:
                results = self.demo.action.package_search(**kwargs, start=counter, rows=1000)
                counter += 1000
                list_of_datasets.extend(results['results'])

        return  list_of_datasets

class CKANGeoService(CKANServiceBase):
    service_name = "ckan_geo_service"
    display_name = "CKAN Geo Service"
    description = 'To grab geo specific packages from a CKAN repository.'
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
        list_of_datasets = self.get_data(extras={"ext_bbox": "-180,-90,180,90"})
        features = pd.DataFrame(list_of_datasets)
        features['extras'] = features['extras'].apply(lambda row: {i['key']: i['value'] for i in row})
        features['geometry'] = features['extras'].apply(lambda r: shape(geojson.loads(r['spatial'])))
        features['service_id'] = features['id'].apply(str)
        features.index = features['service_id']
        features.rename(columns={
            'title': 'display_name',
        }, inplace=True)

        return features


class CKANNormService(CKANServiceBase):
    service_name = "ckan_norm"
    display_name = "CKAN Normal Service"
    description = 'To grab non-geo specific packages from a CKAN repository.'
    service_type = "norm-discrete"
    unmapped_parameters_available = True
    _parameter_map = {}

    def get_features(self, **kwargs):
        list_of_datasets = self.get_data()
        features = pd.DataFrame(list_of_datasets)
        features['service_id'] = features['id'].apply(str)
        features.index = features['service_id']
        features.rename(columns={
            'title': 'display_name',
        }, inplace=True)

        return features


class CKANPublishBase(PublishBase):
    publisher_name = "ckan_pub"
    display_name = "CKAN Publisher"
    description = "To be able to push to the CKAN repository.."

    title = param.String(default="", doc="", precedence=1)
    dataset_name = param.String(default="", doc="", precedence=2)
    author = param.String(default="", doc="", precedence=3)
    author_email = param.String(default="", doc="", precedence=4)
    availability = param.ObjectSelector(default=None, doc="", objects=[True,False], precedence=5)
    description = param.String(default="", doc="", precedence=6)
    type = param.String(default="", doc="Data type", precedence=7)
    dataset = param_util.DatasetListSelector(default=(), filters={'status': 'downloaded'}, precedence=8,
                                             doc="dataset to publish to ckan")
    @property
    def demo(self):
        return self.provider.get_demo()

    def publish(self, options=None):
        try:
            p = param.ParamOverrides(self, options)
            params = {"name": p.dataset_name,
                      "title": p.title,
                      "private": p.availability,
                      "author": p.author,
                      "author_email": p.author_email,
                      "maintainer": p.author,
                      "license_id": "None",
                      "notes": p.description,
                      "type": p.type
                      }

            the_package = self.demo.action.package_create(**params)

            for dataset in p.dataset:
                dataset_metadata = get_metadata(dataset)[dataset]
                fpath = dataset_metadata['file_path']
                filename, file_extension = os.path.splitext(fpath)
                now = datetime.datetime.now()
                params2 = {"package_id": the_package['id'],
                           "format": file_extension,
                           "name": filename,
                           "size": os.path.getsize(fpath),
                           "created": str(now)[:10],
                           "upload": fpath
                           }
                self.demo.action.resource_create(**params2)
            return the_package['id']
        except Exception as e:
            raise e


class CKANProvider(ProviderBase):
    service_base_class = CKANServiceBase
    publisher_base_class = CKANPublishBase
    display_name = 'CKAN Provider'
    description = 'Services avaliable through the CKAN applications.'
    organization_name = 'CKAN'
    organization_abbr = 'CKAN'
    hostname = 'https://demo.ckan.org'

    def authenticate_me(self, **kwargs):

        api_key = getpass("Enter CKAN API key: ")

        db = get_db()
        with db_session:
            p = db.Providers.select().filter(provider=self.name).first()

            provider_metadata = {
                'provider': self.name,
                'username': 'placeholder',
                'password': api_key,
            }

            if p is None:
                db.Providers(**provider_metadata)
            else:
                p.set(**provider_metadata)

        return True

    def get_demo(self):
        api_key = None
        try:
            api_key = self.credentials['password']
        except ValueError:
            pass  # ignore error if api_key has not been stored

        demo = RemoteCKAN(address=self.hostname, apikey=api_key)
        demo.action.package_search(rows=1)
        return demo

    def get_ckan_status(self):
        demo = self.get_demo()
        status = demo.action.status_show()
        # check if status contains spatial_query_extension.
