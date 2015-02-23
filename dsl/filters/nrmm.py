"""NRMM Filter

"""

from .base import FilterBase

class NrmmFromVITD(FilterBase):
    def register(self):
        """Register VITD to NRMM Filter

        """
        self.schema = {}

        self.operates_on = {
            'datatype': 'terrain-vitd',
            'geotype': 'polygon',
            'parameters': 'terrain-nrmm',
        }
        self.produces = {
            'datatype': 'terrain-nrmm',
            'geotype': 'polygon',
            'parameters': 'nrmm',
        }


    def apply(**kwargs):
        pass

    def apply_options(**kwargs):
        pass