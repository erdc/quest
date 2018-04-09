from .base import ProviderBase, ServiceBase, PublishBase
from ..api.metadata import get_metadata
from shapely.geometry import box
from ckanapi import RemoteCKAN
from ..util import param_util
import pandas as pd
import param


class CKANServiceBase(ServiceBase):
    service_name = "ckan_service"
    display_name = "CKAN Service"
    description = 'To grab the single service from the CKAN repository.'
    service_type = "norm-discrete"
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    feature_id = "ckan"
    _parameter_map = {}

    api_key = param.String(default=None, doc="user api key", precedence=1)
    address = param.String(default=None, doc="Website URL", precedence=2)

    def get_features(self, **kwargs):
        the_feature = {"service_id": "ckan", "display_name": "ckan", "geometry": box(-180, -90, 180, 90)}
        feature = pd.DataFrame(the_feature, index=[0])
        return feature

    def download(self, feature, file_path, dataset, **params):
        pass
        # p = param.ParamOverrides(self, params)
        # demo = RemoteCKAN(address=p.address, apikey=p.api_key)

        # Have to figure out what the user wants to grab and pull.

        # results = ncep.get_ncep_product_data(ncep_provider="Global Forecast System", product_type=p.type,
        #                                      product_date=p.date, resolution=p.res, cycle_runtime=p.cycle,
        #                                      forecast_start=p.start, forecast_end=p.end, product_format=p.format,
        #                                      name_of_product=p.product)
        # print(results)
        # if len(results) > 0:
            # ncep.download_data(file_path, results)
        #     metadata = {
        #         'metadata': results,
        #         'file_path': file_path,
        #         'file_format': 'unknown',
        #         'datatype': 'unknown',
        #         'parameter': "unknown",
        #         'unit': "unknown",
        #     }
        # else:
        #     raise ValueError("There is no data found on those parameters.")
        #
        # return metadata


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

    # Do we even need this?
    def __init__(self, provider, **kwargs):
        super(CKANPublishBase, self).__init__(provider, **kwargs)

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

            the_resource = demo.action.package_create(**params)

            for dataset in p.dataset:
                dataset_metadata = get_metadata(dataset)[dataset]
                fpath = dataset_metadata['file_path']
                # Need to push the data to the folder.
            return the_resource['id']
        except Exception as e:
            raise e

class NCEPProvider(ProviderBase):
    # Why is one in a list again and one is not?
    service_base_class = CKANServiceBase
    publishers_list = [CKANPublishBase]
    display_name = 'CKAN Provider'
    description = 'Services avaliable through the CKAN applications.'
    organization_name = 'CKAN'
    organization_abbr = 'CKAN'

