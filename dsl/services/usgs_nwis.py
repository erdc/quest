from dsl.services import base
from ulmo.usgs import nwis

class UsgsNwisIV(base.DataServiceBase):
    def register(self):
        """Register USGS NWIS IV plugin by setting service name, source and uid 
        """
        self.metadata = {
                    'provider': {'name': 'United States Geological Survey NWIS', 'id': 'usgs-nwis'},
                    'dataset_name': 'instantaneous values service',
                    'description': 'instantaneous values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries',
                }


    def get_locations(self, sites=None, state_code=None, site_type=None, service='iv'):
        locations = nwis.get_sites(sites=sites, state_code=state_code, site_type=site_type, service=service)
        return locations


class UsgsNwisDV(base.DataServiceBase):
    def register(self):
        """Register USGS NWIS DV plugin by setting service name, source and uid 
        """
        self.metadata = {
                    'provider': {'name': 'United States Geological Survey NWIS', 'id': 'usgs-nwis'},
                    'dataset_name': 'daily values service',
                    'description': 'daily values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries',
                }


    def get_locations(self, sites=None, state_code=None, site_type=None, service='dv'):
        locations = nwis.get_sites(sites=sites, state_code=state_code, site_type=site_type, service=service)
        return locations