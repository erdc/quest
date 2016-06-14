from .dl_base import DatalibraryBase

class Vitd2Nrmm(DatalibraryBase):
    def register(self, name=None):
        """Register Timeseries

        """
        self.name = name
        self.template = 'vitd2nrmm.txt'
        self.metadata = {
            'group': 'vitd',
            'operates_on': {
                'datatype': 'vitd',
                'geotype': 'Polygon',
                'parameters': 'vitd',
            },
            'produces': {
                'datatype': 'nrmm',
                'geotype': 'Polygon',
                'parameters': 'nrmm',
            },
        }

    def apply_filter_options(self):
        return {}

    def _new_dataset_metadata(self):
        return {
            'parameter': 'nrmm',
            'datatype': 'nrmm',
            'file_format': 'nrmm',
        }
