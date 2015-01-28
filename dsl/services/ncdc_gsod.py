from data_services_library.services import base


class NcdcGsod(base.DataServiceBase):
    def register(self):
        """Register NCDC GSOD plugin by setting service name, source and uid 
        """
        self.metadata = {
                    'provider': {'name': 'National Climatic Data Center (NCDC)', 'id': 'ncdc'},
                    'dataset_name': 'Global Summary of the Day',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                }