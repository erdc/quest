"""
Example Services

DEPRECIATED .... NOT CURRENTLY WORKING WITH NEW API
NEW VERSION INSIDE DATALIBRARY

"""

from dsl.filters import base
from geojson import Feature, FeatureCollection, Point, Polygon
from random import random


class Basic(base.DataFilterBase):
    def register(self):
        """Register Basic VITD Filter
        """

        schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "title": "Filter Options",
            "properties": {
                "options": {
                    "type": "array",
                    "items": [
                        {
                            "name": "Grid Size",
                            "value": {
                                "type": "integer",
                                "enum": [5, 10, 20, 50, 100],
                                "default": 5
                            }
                        },
                        {
                            "name": "Timeout Seconds",
                            "value": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "exclusiveMinimum": True,
                                    "maximum": 3600.0,
                                    "default": 10.0
                            }
                        },
                        {
                            "name": "Output Name",
                            "value": {
                                "type": "string",
                                "default": "DSL Output"
                            }
                        },
                        {
                            "name": "Notify",
                            "value": {
                                "type": "boolean",
                                "default": False
                            }
                        }
                    ]
                }
            }
        }

        self.metadata = {
                    'filter_name': 'Basic VITD Filter',
                    'description': 'Runs VITD processing algorithm',
                    'type': 'vitd',
                    'schema': schema,
                }
