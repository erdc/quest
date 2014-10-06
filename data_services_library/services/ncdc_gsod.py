from data_services_library.services import base


class NcdcGhcn(base.DataServiceBase):
    def register(self):
        """Register NCDC GSOD plugin by setting service name, source and uid 
        """
        self.source = 'NCDC'
        self.service_name = 'NCDC GSOD Service'
        self.uid = 'ncdc-gsod'
        self.metadata = {
                    'uid' : 'ncdc-gsod',
                    'name': 'Global Summary of the Day service',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }