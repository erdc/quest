from .dl_base import DatalibraryBase
import os

class Vitd2Nrmm(DatalibraryBase):
    def register(self, name='Vitd2Nrmm'):
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

    def apply_filter_options(self, fmt='json-schema'):
        if fmt == 'json-schema':
            schema = {}

        if fmt == 'smtk':
            schema = ''

        return schema

    def _new_dataset_metadata(self):
        return {
            'parameter': 'nrmm',
            'datatype': 'nrmm',
            'file_format': 'nrmm',
        }


class Vitd2Raster(DatalibraryBase):
    def register(self, name='Vitd2Raster'):
        """Register Vitd2Raster.

        SLP == slope
        VEG == vegetation
        SMC == soil material composition
        SDR == surface drainage
        TRN == transportation
        OBS == obstacles
        """
        self.name = name
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

    def apply_filter_options(self, fmt='json-schema'):
        if fmt == 'json-schema':
            properties = {
                "theme": {
                    "type": {
                        "enum": [
                            'slope',
                            'vegetation',
                            'soil_material_composition',
                            'surface_drainage',
                            'transportation',
                            'obstacles',
                        ],
                        "default": 'daily'
                    },
                    "description": "Theme to Extract from VITD",
                },
            }

            schema = {
                "title": "VITD2Raster Filter",
                "type": "object",
                "properties": properties,
            }

        if fmt == 'smtk':
            schema = ''

        return schema

    def _new_dataset_metadata(self):

        self.save_path = os.path.join(self.save_path, '{}.tiff'.format(self.parameter))
        return {
            'parameter': self.parameter,
            'datatype': 'raster',
            'file_format': 'raster-gdal',
        }

    def _extra_options(self, options):
        """override in inherited classes if more options need to be set"""
        self.parameter = options.pop('theme').lower()
        attr_dict = {
            'slope': 'SLP',
            'vegetation': 'VEG',
            'soil_material_composition': 'SMC',
            'surface_drainage': 'SDR',
            'transportation': 'TRN',
            'obstacles': 'OBS',
        }

        attr = attr_dict[self.parameter]
        theme = attr.lower()
        filename = self.parameter
        options.update({'theme': theme, 'attr': attr, 'filename': filename})
        return options