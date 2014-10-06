from data_services_library.services import base


class UsgsNwisIV(base.DataServiceBase):
    def register(self):
        """Register USGS NWIS plugin by setting service name, source and uid 
        """
        self.source = 'USGS'
        self.service_name = 'USGS NWIS Web Services'
        self.uid = 'usgs-nwis-iv'
        self.metadata = {
                    'uid' : 'usgs-nwis-iv',
                    'name': 'instantaneous values service',
                    'description': 'instantaneous values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }


class UsgsNwisDV(base.DataServiceBase):
    def register(self):
        """Register USGS NWIS plugin by setting service name, source and uid 
        """
        self.source = 'USGS'
        self.service_name = 'USGS NWIS Web Services'
        self.uid = 'usgs-nwis-dv'
        self.metadata = {
                    'uid' : 'usgs-nwis-dv',
                    'name': 'daily values service',
                    'description': 'daily values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }