from quest.plugins import ProviderBase, ServiceBase
from ncep_client import NCEP_Client
from shapely.geometry import box
import pandas as pd
import param


class NCEPServiceBase(ServiceBase):

    def get_features(self, **kwargs):
        the_feature = {"service_id": "ncep", "display_name": "ncep", "geometry": box(-180, -90, 180, 90)}
        feature = pd.DataFrame(the_feature, index=[0])
        return feature


class NCEP_GFS_Service(NCEPServiceBase):
    ncep = NCEP_Client()
    service_name = "ncep_gfs"
    display_name = "NCEP GFS Service"
    description = 'NCEP GFS is a noaa repository for global weather data.'
    service_type = "norm-discrete"
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    feature_id = "ncep"
    # These are slowing down the api because it has to load the web page.
    _possible_types = sorted(ncep.get_provider_types("Global Forecast System"))
    _possible_products = sorted(ncep.get_provider_products("Global Forecast System"))
    _possible_formats = sorted(ncep.get_formats_of_a_product("Global Forecast System"))
    _parameter_map = {}

    date = param.String(default=None, doc="YYYYMMDD", precedence=1)
    res = param.String(default=None, doc="Froecast Resolution", precedence=2)
    cycle = param.String(default=None, doc="Forecast Cycle Runtime", precedence=3)
    start = param.String(default=None, doc="Forecast start time (f###)", precedence=4)
    end = param.String(default=None, doc="Forecast end time (f###)", precedence=5)
    format = param.ObjectSelector(default=None, doc="Paramerter", objects=_possible_formats, precedence=6)
    type = param.ObjectSelector(default=None, doc="Parameter2", objects=_possible_types, precedence=7)
    product = param.ObjectSelector(default=None, doc="Parameter3", objects=_possible_products, precedence=8)

    def download(self, feature, file_path, dataset, **params):
        ncep = NCEP_Client()
        p = param.ParamOverrides(self, params)

        if p.product == "GFS" or p.product == "GDAS":
            raise ValueError("Please specify a specific product not GFS or GDAS")

        results = ncep.get_ncep_product_data(ncep_provider="Global Forecast System", product_type=p.type,
                                             product_date=p.date, resolution=p.res, cycle_runtime=p.cycle,
                                             forecast_start=p.start, forecast_end=p.end, product_format=p.format,
                                             name_of_product=p.product)
        print(results)
        if len(results) > 0:
            ncep.download_data(file_path, results)
            metadata = {
                'metadata': results,
                'file_path': file_path,
                'file_format': 'weather-specific',
                'datatype': 'weather',
                'parameter': "ncep_parameter",
                'unit': "unkown",
            }
        else:
            raise ValueError("There is no data found on those parameters.")

        return metadata


class NCEP_NAM_Service(NCEPServiceBase):
    ncep = NCEP_Client()
    service_name = "ncep_nam"
    display_name = "NCEP NAM Service"
    description = 'NCEP NAM is a noaa repository for global weather data.'
    service_type = "norm-discrete"
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    feature_id = "ncep"
    # These are slowing down the api because it has to load the web page.
    _possible_types = sorted(ncep.get_provider_types("North American Model"))
    _possible_products = sorted(ncep.get_provider_products("North American Model"))
    _possible_formats = sorted(ncep.get_formats_of_a_product("North American Model"))
    _parameter_map = {}

    date = param.String(default=None, doc="YYYYMMDD", precedence=1)
    res = param.String(default=None, doc="Froecast Resolution", precedence=2)
    cycle = param.String(default=None, doc="Forecast Cycle Runtime", precedence=3)
    start = param.String(default=None, doc="Forecast start time (f###)", precedence=4)
    end = param.String(default=None, doc="Forecast end time (f###)", precedence=5)
    format = param.ObjectSelector(default=None, doc="Paramerter", objects=_possible_formats, precedence=6)
    type = param.ObjectSelector(default=None, doc="Parameter2", objects=_possible_types, precedence=7)
    product = param.ObjectSelector(default=None, doc="Parameter3", objects=_possible_products, precedence=8)

    def download(self, feature, file_path, dataset, **params):
        ncep = NCEP_Client()
        p = param.ParamOverrides(self, params)

        if p.product == "NAM":
            raise ValueError("Please specify a specific product not NAM")

        results = ncep.get_ncep_product_data(ncep_provider="North American Model", product_type=p.type,
                                             product_date=p.date, resolution=p.res, cycle_runtime=p.cycle,
                                             forecast_start=p.start, forecast_end=p.end, product_format=p.format,
                                             name_of_product=p.product)
        print(results)
        if len(results) > 0:
            ncep.download_data(file_path, results)
            metadata = {
                'metadata': results,
                'file_path': file_path,
                'file_format': 'weather-specific',
                'datatype': 'weather',
                'parameter': "ncep_parameter",
                'unit': "unkown",
            }
        else:
            raise ValueError("There is no data found on those parameters.")

        return metadata


class NCEPProvider(ProviderBase):
    service_base_class = NCEPServiceBase
    display_name = 'NCEP Provider'
    description = 'Services avaliable through the NOAA NCEP Server.'
    organization_name = 'National Centers for Environmental Prediction'
    organization_abbr = 'NCEP'
    name = 'noaa-ncep'
