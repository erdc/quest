"""I/O plugin for Geojson with timeseries


"""
from .base import IoBase
from .. import util
from geojson import Feature, Point, dump
import json
import os
import pandas as pd


class TsGeojson(IoBase):
    """Base class for I/O for different file formats
    """

    def register(self):
        """Register plugin by setting description and io type 
        """
        self.description = 'Reader/Writer for Geojson with timeseries in properties field'
        self.iotype = 'timeseries' 

    def read(self, path, as_dataframe=False):
        """Read data from format
        """
        with open(path) as f:
            data = json.load(f)

        if as_dataframe:
            data['values'] = pd.Series(data=data['values'], index=data['time'])
            del data['time']

        return data

    def write(self, path, location, name, longitude, latitude, parameter, unit, df, metadata=None):
        """Write data to format
        """

        feature = Feature(id=location,
                        geometry=Point((float(longitude),
                                        float(latitude))),
                        properties={
                            'name': name,
                            'parameter': parameter,
                            'metadata': metadata,
                            'unit_of_measurement': unit,
                            'time': df.index.to_native_types(),
                            'values': df.values.tolist(),
                        },
                    )
        if not path.endswith('.json'):
            path += '.json'

        base, fname = os.path.split(path)
        util.mkdir_if_doesnt_exist(base)

        with open(path, 'w') as f:
            dump(feature, f)

        print 'file written to: %s' % path
