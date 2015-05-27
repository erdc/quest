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

    def read(self, path, as_dataframe=True):
        """Read data from format
        """
        with open(path) as f:
            data = json.load(f)

        if as_dataframe:
            properties = data.pop('properties')
            metadata = properties.pop('metadata', None)
            time = properties.pop('time')
            df = pd.DataFrame(data=properties, index=pd.to_datetime(time))
            df.convert_objects(convert_numeric=True)
            df.sort(inplace=True)
            df.metadata = metadata
            df.feature = data
            data = df

        return data

    def write(self, path, location_id, geometry, dataframe, metadata=None):
        """Write data to format
        """

        # replace NaN values with None
        dataframe = dataframe.where(pd.notnull(dataframe), None)
        
        properties={
            'time': dataframe.index.to_native_types().tolist(),
            'metadata': metadata,
        }

        for parameter in dataframe.columns:
            properties.update({parameter: dataframe[parameter].tolist()})

        feature = Feature(id=location_id,
                        geometry=geometry,
                        properties=properties,
                    )
        if not path.endswith('.json'):
            path += '.json'

        base, fname = os.path.split(path)
        util.mkdir_if_doesnt_exist(base)

        with open(path, 'w') as f:
            dump(feature, f)

        print 'file written to: %s' % path
