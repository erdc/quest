from data_services_library.services import base


class NcdcGhcn(base.DataServiceBase):
    def register(self):
        """Register NCDC GHCN plugin by setting service name, source and uid 
        """
        self.source = 'NCDC'
        self.service_name = 'NCDC GHCN Service'
        self.uid = 'ncdc-ghcn'
        self.metadata = {
                    'uid' : 'ncdc-ghcn',
                    'name': 'Global Historic Climate Network service',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }