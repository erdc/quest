import os

import param

from .dl_base import DatalibraryBase

class Vitd2Nrmm(DatalibraryBase):
    _name = 'Vitd2Nrmm'

    def register(self, name='Vitd2Nrmm'):
        """Register Timeseries

        """
        # self.name = name
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

    def _new_dataset_metadata(self):
        return {
            'parameter': 'nrmm',
            'datatype': 'nrmm',
            'file_format': 'nrmm',
        }


class Vitd2Raster(DatalibraryBase):
    _name = 'Vitd2Raster'
    theme = param.ObjectSelector(default='vegetation',
                                 doc="""Theme to Extract from VITD""",
                                 objects=[
                                     'slope',
                                     'vegetation',
                                     'soil_material_composition',
                                     'surface_drainage',
                                     'transportation',
                                     'obstacles',
                                 ])

    def register(self, name='Vitd2Raster'):
        """Register Vitd2Raster.

        SLP == slope
        VEG == vegetation
        SMC == soil material composition
        SDR == surface drainage
        TRN == transportation
        OBS == obstacles
        """
        # self.name = name
        self.template = 'vitd2raster.txt'
        self.metadata = {
            'group': 'vitd',
            'operates_on': {
                'datatype': 'vitd',
                'geotype': 'Polygon',
                'parameters': 'vitd',
            },
            'produces': {
                'datatype': 'raster',
                'geotype': 'Polygon',
                'parameters': [
                    'slope',
                    'vegetation',
                    'soil_material_composition',
                    'surface_drainage',
                    'transportation',
                    'obstacles',
                ],
            },
        }

    def _new_dataset_metadata(self):

        self.file_path = os.path.join(self.file_path, '{}.tiff'.format(self.parameter))
        return {
            'parameter': self.parameter,
            'datatype': 'raster',
            'file_format': 'raster-gdal',
        }

    def _extra_options(self, options):
        """override in inherited classes if more options need to be set"""
        self.parameter = options.pop('theme').lower()
        attr_dict = {
            'slope': ('slp', 'SLP'),
            'vegetation': ('veg', 'VEG'),
            'soil_material_composition': ('smc', 'STP'),
            'surface_drainage': ('sdr', 'SDR'),
            'transportation': ('trn', 'TRN'),
            'obstacles': ('obs', 'OBS'),
        }

        theme, attr = attr_dict[self.parameter]
        filename = self.parameter
        options.update({'theme': theme, 'attr': attr, 'filename': filename})
        return options