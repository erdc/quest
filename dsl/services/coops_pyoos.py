import csv
import cStringIO
import os
from geojson import Feature, FeatureCollection, Point
from datetime import datetime
import dateutil.parser as duparser
from .. import util
from pyoos.collectors.coops.coops_sos import CoopsSos

class CoopsPyoos():
    def register(self):
        """Register CO-OPS SOS plugin  
        """
        
        self.collectorCOOPS = CoopsSos()
        self.metadata = {
                    'provider': {
                         'abbr': 'CO-OPS',
                         'name': 'NOAA Center for Operational Oceanographic Products and Services (CO-OPS) SOS',
                        },
                    'dataset_name': 'NOAA CO-OPS Sensor Observation Service',
                    'description': 'NOAA CO-OPS Sensor Obersvation Service',
                    'geographical area': 'Worldwide',
                    'bounding_boxes': [[-177.372, -18.1333, 178.425, 71.3601]], 
                    'geotype': 'points',
                    'datatype': 'timeseries' 
                }
                
    def get_locations(self, locations=None, bounding_box=None):
        
        try :
            
            features = []            
            
            if locations:
                
                if ',' in locations: 
                    station_ids = locations.split(',')        

                    for station_id in station_ids:
                        features.append(_getFeature(self, station_id.strip()))

                else:
                    features.append(_getFeature(self, locations))
    
                return FeatureCollection(features)   
                
            else:
                  
                if bounding_box is None:
                    bounding_box = self.metadata['bounding_boxes'][0]                 
                
                xmin, ymin, xmax, ymax = [float(p) for p in bounding_box]
        
                for offeringID in self.collectorCOOPS.server.contents.keys():
                    if not 'network' in offeringID:        
                        stationID = offeringID.split('-')[1]
                    
                        offeringid = 'station-%s' % stationID            
            
                        station = self.collectorCOOPS.server.contents[offeringid]
            
                        x, y = station.bbox[:2]

                        if x >= xmin and x <= xmax and y >= ymin and y <= ymax:
                            features.append(_getFeature(stationID))
                            
                return FeatureCollection(features)
                
        except Exception, e:
            print str(e)
        
    def get_locations_filters(self):
        schema = {
            "title": "Location Filters",
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "Optional single or comma delimited list of location identifiers",
                    },
                "bounding_box": {
                    "type": "string",
                    "description": "bounding box should be a comma delimited set of 4 numbers ",
                    },
            },
            "required": None,
        }
        return schema        
        
    def get_data(self, locations, variable, start_date=None, end_date=None, dataType=None, datum=None, path=None):
       
        try:        
        
            if start_date is not None:
                # date is in Year-Month-Day format, (Ex: 2012-10-01)
                self.collectorCOOPS.start_time = datetime.strptime(start_date, "%Y-%m-%d")
            
            if end_date is not None:
                self.collectorCOOPS.end_time = datetime.strptime(end_date, "%Y-%m-%d")

            if locations is None:
                raise ValueError("A location needs to be supplied.")
               
            if variable is None:   
                raise ValueError("An observed property or variable needs to be supplied.")
            
            self.collectorCOOPS.features  = [locations]  #station id or network id 
            self.collectorCOOPS.variables = ['http://mmisw.org/ont/cf/parameter/' + variable]
        
            self.collectorCOOPS.dataType = dataType
            
            self.collectorCOOPS.datum = datum           
                    
            response = self.collectorCOOPS.raw(responseFormat="text/csv")
        
            filename = 'station-' + locations + '_' + variable + '.csv'
    
            if not path:
                path = util.get_dsl_dir()
    
            if not os.path.exists(path):
                os.makedirs(path)
            
            #write out a csv file for now but create a plugin to write out this data
                
            csvFile_path = os.path.join(path, filename)

            with open(csvFile_path, 'w') as f:
                f.write(response)        
        
        except Exception, e: 
            print str(e)
            
    def get_data_filters(self):
        schema = {
            "title": "Download Options",
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "single or comma delimited list of location identifiers to download data for",
                },
                "variable": {
                    "type": "string",
                    "description": "the variable or observed property used for the data search"
                },
                "start_date": {
                    "type": "string",
                    "description": "start date to begin the data search"
                },
                "end_date": {
                    "type": "string",
                    "description": "end date to end the data search"
                },
                "data_type": {
                    "enum": [ "PreliminarySixMinute", "PreliminaryOneMinute", "VerifiedSixMinute", "VerifiedHourlyHeight", "VerifiedHighLow", "VerifiedDailyMean"],
                    "description": "Optional value for data type"
                },   
                "datum": {
                    "enum": [ "IGLD", "MHHW", "MHW", "MLLW", "MLW", "MSL", "MTL", "NAVD", "STND" ],
                    "description": "Optional value for datum"
                },                             
                "path": {
                    "type": "string",
                    "description": "base file path to store data"
                },
            },
            "required": ["locations", "variable"],
        }
        return schema
        
    def provides(self):
        return ['tidal elevation']
        
def _getFeature(self, stationID):
        
    offeringid = 'station-%s' % stationID
        #print offeringid in collectorndbc.server.contents.keys()
    
    variables_list = []
    
    station = self.collectorCOOPS.server.contents[offeringid]
        #print 'ofr.id = %s, ofr.bbox = %s, ofr.c41012.observed_properties = %s' % (ofr.id, ofr.bbox, ofr.observed_properties) 
    
    for op in station.observed_properties:
        variables = op.split("/")
        variables_list.append(variables[len(variables) - 1])
       
    properties = {
                  'station_name': station.name,
                  'station_description': station.description,
                  'data_offered': variables_list,
                  }
       
    feature = Feature(geometry=Point(station.bbox[:2]), properties=properties, id=stationID)
        
    return feature    
 
     
      