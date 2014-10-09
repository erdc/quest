from data_services_library.services import base


class NcdcGhcn(base.DataServiceBase):
    def register(self):
        """Register NCDC GHCN plugin by setting service name, source and uid 
        """
        self.metadata = {
                    'service_name': 'NCDC',
                    'dataset_name': 'Global Historic Climate Network',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }