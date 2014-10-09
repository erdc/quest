from data_services_library.services import base


class NcdcGsod(base.DataServiceBase):
    def register(self):
        """Register NCDC GSOD plugin by setting service name, source and uid 
        """
        self.metadata = {
                    'service_name': 'NCDC',
                    'dataset_name': 'Global Summary of the Day',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }