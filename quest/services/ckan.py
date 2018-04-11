from .base import ProviderBase, ServiceBase, PublishBase
from ..api.metadata import get_metadata
from shapely.geometry import Point, box
from ckanapi import RemoteCKAN
from ..util import param_util
import pandas as pd
import datetime
import param
import os

class CKANServiceBase(ServiceBase):

    def get_features(self, **kwargs):
        raise NotImplementedError()

    api_key = param.String(default=None, doc="user api key", precedence=1)
    address = param.String(default=None, doc="Website URL", precedence=2)

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
        p = param.ParamOverrides(self, kwargs['options'])
        try:
            if p.api_key is None:
                demo = RemoteCKAN(address=p.address)
            else:
                demo = RemoteCKAN(address=p.address, apikey=p.api_key)
        except:
            raise ValueError("Not able to connect to the CKAN instance.")

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
        results = demo.action.package_search(start=0, rows=1000)
        list_of_datasets = results['results']
        if results['count'] > 1000:
            counter = 1001
            total_datasets = results['count']
            while counter < total_datasets:
                results = demo.action.package_search(start=counter, rows=1000)
                counter += 1001
                list_of_datasets.append(results['results'])

        features = pd.DataFrame(list_of_datasets)
        features['geometry'] = features['extras'].apply(self.parse_coverages)
        features['service_id'] = features['resource_id'].apply(str)
        features.index = features['service_id']
        features.rename(columns={
            'title': 'display_name',
        }, inplace=True)

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


class CKANNormService(CKANServiceBase):
    service_name = "ckan_norm"
    display_name = "CKAN Normal Service"
    description = 'To grab non-geo specific packages from a CKAN repository.'
    service_type = "norm-discrete"
    unmapped_parameters_available = True
    _parameter_map = {}

    def get_features(self, **kwargs):
        p = param.ParamOverrides(self, kwargs['options'])
        try:
            if p.api_key is None:
                demo = RemoteCKAN(address=p.address)
            else:
                demo = RemoteCKAN(address=p.address, apikey=p.api_key)
        except:
            raise ValueError("Not able to connect to the CKAN instance.")

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
        results = demo.action.package_search(start=0, rows=1000)
        list_of_datasets = results['results']
        if results['count'] > 1000:
            counter = 1001
            total_datasets = results['count']
            while counter < total_datasets:
                results = demo.action.package_search(start=counter, rows=1000)
                counter += 1001
                list_of_datasets.append(results['results'])

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

    api_key = param.String(default=None, doc="", precedence=1)
    address = param.String(default=None, doc="", precedence=2)
    name = param.String(default="", doc="", precedence=3)
    title = param.String(default="", doc="", precedence=4)
    author = param.String(defualt="", doc="", precedence=5)
    author_email = param.String(default="", doc="", precedence=6)
    availability = param.ObjectSelector(default=None, doc="", objects=[True,False], precedence=7)
    description = param.String(default="", doc="", precedence=8)
    type = param.String(default="", doc="Data type", precedence=9)
    dataset = param_util.DatasetListSelector(default=(), filters={'status': 'downloaded'}, precedence=10,
                                             doc="dataset to publish to ckan")

    def publish(self, options=None):
        try:
            p = param.ParamOverrides(self, options)
            demo = RemoteCKAN(address=p.address, apikey=p.api_key)
            params = {"name": p.name,
                      "title": p.title,
                      "private": p.availability,
                      "author": p.author,
                      "author_email": p.author_email,
                      "maintainer": p.author,
                      "license_id": "None",
                      "notes": p.description,
                      "type": p.type
                      }

            the_package = demo.action.package_create(**params)

            for dataset in p.dataset:
                dataset_metadata = get_metadata(dataset)[dataset]
                fpath = dataset_metadata['file_path']
                filename, file_extension = os.path.splitext(fpath)
                now = datetime.datetime.now()
                params2 = {"package_id": the_package['id'],
                           "format": file_extension,
                           "name": filename,
                           "size": os.path.getsize(fpath),
                           "created": str(now)[:10]
                           }
                demo.action.resource_create(**params2)
            return the_package['id']
        except Exception as e:
            raise e


class NCEPProvider(ProviderBase):
    service_base_class = CKANServiceBase
    publishers_base_class = CKANPublishBase
    display_name = 'CKAN Provider'
    description = 'Services avaliable through the CKAN applications.'
    organization_name = 'CKAN'
    organization_abbr = 'CKAN'
