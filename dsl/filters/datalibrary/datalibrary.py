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
            properties = {
                "apply_to_collection": {
                    "type": {'enum': ['yes', 'no'], 'default': 'no'},
                    "description": "Apply filter to all tiles in collection",
                },
                "apply_to_collection_flag": {
                    "type": 'boolean',
                    "description": "Apply filter to all tiles in collection",
                    "default": False,
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
                "apply_to_collection": {
                    "type": {'enum': ['yes', 'no'], 'default': 'no'},
                    "description": "Apply filter to all tiles in collection",
                },
                "apply_to_collection_flag": {
                    "type": 'boolean',
                    "description": "Apply filter to all tiles in collection",
                    "default": False,
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