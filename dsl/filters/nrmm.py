"""NRMM Filter

"""

from .base import FilterBase
from ..api import get_collection, add_to_collection
from .. import util
from geojson import Polygon, Feature, FeatureCollection
import numpy as np
import os
import time

class NrmmFromVITD(FilterBase):
    def register(self):
        """Register VITD to NRMM Filter

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['terrain-vitd'],
                'geotype': ['polygon'],
                'parameters': ['terrain-nrmm'],
            },
            'produces': {
                'datatype': 'terrain-nrmm',
                'geotype': 'polygon',
                'parameters': 'nrmm',
            },
        }


    def apply_filter(self, collection_name, **kwargs):
        available_themes = self.get_themes().keys()

        themes = []
        for k, v in kwargs.items():
            if k in available_themes:
                if v:
                    themes.append(k)

        if themes == []:
            themes = available_themes

        themes = ','.join(themes)
        collection = get_collection(collection_name)

        #calculate bounding box
        locations = collection['datasets']['iraq-vitd']['locations']['features']
        locs = np.hstack([loc['geometry']['coordinates'] for loc in locations]).squeeze()
        lons = locs[:,0]
        lats = locs[:,1]
        xmin, xmax = lons.min(), lons.max()
        ymin, ymax = lats.min(), lats.max()
        bounding_box = ','.join([str(n) for n in [xmin, ymin, xmax, ymax]])
        nrmm_id = 'nrmm-%s' % (bounding_box)
        util.mkdir_if_doesnt_exist(os.path.join(collection['path'], 'nrmm'))
        dest = 'nrmm/data-%s.dat' % nrmm_id
        open(os.path.join(collection['path'], dest), 'w').close() #make fake empty file
        properties = {'metadata': 'generated using vitd2nrmm plugin', 'relative_path': dest}
        new_locs = FeatureCollection([Feature(geometry=Polygon([util.bbox2poly(xmin, ymin, xmax, ymax)]), properties=properties, id=nrmm_id)])
        path = collection['path']        
        vitd_dir = os.path.join(path, 'nga/iraq/vitd')
        #call plugin.
        print 'calling VITD to NRMM plugin for bounding box - %s, with themes - %s' % (bounding_box, themes)
        time.sleep(10)
        print 'nrmm file written to: %s' % os.path.join(path, dest)
        collection = add_to_collection(collection_name, 'local', new_locs, parameters='terrain-nrmm')
        return collection

    def apply_filter_options(self, **kwargs):
        themes = self.get_themes()
        properties = {
            "collection_name": {
                "type": "string",
                "description": "Name of collection",
            }, 
        }
        for k, v in themes.iteritems():
            properties.update({
                    k: {
                        "type": "boolean",
                        "description": v,    
                    } 
                })

        schema = {
            "title": "Download Options",
            "type": "object",
            "properties": properties,
            "required": ["collection_name"],
        }
        
        return schema

    def get_themes(self): #, filename):
        #with open(filename) as f:
        #    s = filter(lambda x: x in string.printable, f.read())
        #
        #s = s.split(';')[-1]
        #return {s[x:x+58][:3]:s[x:x+58][3:].strip() for x in range(0, len(s), 58)}
        themes = {
            'obs': 'Obstacles',
            'sdr': 'Surface Drainage',
            'slp': 'Slope/Surface Configuration',
            'smc': 'Soils/Surface Materials',
            'trn': 'Transportation',
            'veg': 'Vegetation'
        }

        return themes