
from .base import DataServiceBase
import os
from geojson import Feature, FeatureCollection, Point
from datetime import datetime
from .. import util
from pyoos.collectors.coops.coops_sos import CoopsSos

class CoopsPyoos(DataServiceBase):
    def register(self):
        """Register CO-OPS SOS plugin  
        """
        
        self.metadata = {
                    'provider': {
                         'abbr': 'CO-OPS',
                         'name': 'NOAA Center for Operational Oceanographic Products and Services (CO-OPS) SOS',
                        },
                    'display_name': 'NOAA CO-OPS Sensor Observation Service',
                    'service': 'NOAA CO-OPS Sensor Observation Service',
                    'description': 'NOAA CO-OPS Sensor Obersvation Service',
                    'geographical area': 'Worldwide',
                    'bounding_boxes': [[-177.372, -18.1333, 178.425, 71.3601]], 
                    'geotype': 'points',
                    'datatype': 'timeseries' 
                }
                
    def get_locations(self, locations=None, bounding_box=None):
        
        try :
            
            if not hasattr(self, 'collectorCOOPS'):
                self.collectorCOOPS = CoopsSos()
            
            features = []            
            
            if locations:
                
                for location in locations:
                    features.append(self._getFeature(location))
                    
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
                            features.append(self._getFeature(stationID))
                            
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
        
    def get_data(self, locations, parameters=None, start_date=None, end_date=None, data_type=None, datum=None, path=None):
       
        try:        
            
            if not hasattr(self, 'collectorCOOPS'):
                self.collectorCOOPS = CoopsSos()
        
            if start_date is not None:
                # date is in Year-Month-Day format, (Ex: 2012-10-01)
                self.collectorCOOPS.start_time = datetime.strptime(start_date, "%Y-%m-%d")
            
            if end_date is not None:
                self.collectorCOOPS.end_time = datetime.strptime(end_date, "%Y-%m-%d")

            if locations is None:
                raise ValueError("A location needs to be supplied.")
            
            parameters = 'water_surface_height_above_reference_datum'
                        
            self.collectorCOOPS.variables = ['http://mmisw.org/ont/cf/parameter/' + parameters]
        
            self.collectorCOOPS.dataType = data_type
            
            self.collectorCOOPS.datum = datum           
                                        
            if not path:
                path = util.get_dsl_dir()
                    
            if not os.path.exists(path):
                os.makedirs(path)
                    
            data_files = {}

            for location in locations:    
                
                data_files[location] = {}
                       
                self.collectorCOOPS.features = [location]  #station id or network id                     
                    
                response = self.collectorCOOPS.raw(responseFormat="text/csv")
        
                filename = 'station-%s_%s.csv' % (location, parameters)
                       
                #write out a csv file for now but create a plugin to write out this data
                
                csvFile_path = os.path.join(path, filename)

                with open(csvFile_path, 'w') as f:
                    f.write(response)        
        
                data_files[location][parameters] = filename        
        
            return data_files        
            
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
                "parameters": {
                     "type": "string",
                    "description": "single or comma delimited list of parameters to download data for"
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
                    "enum": [ "PreliminarySixMinute", "PreliminaryOneMinute", "VerifiedSixMinute", "VerifiedHourlyHeight", "VerifiedHighLow",
                              "VerifiedDailyMean", "SixMinuteTidePredictions", "HourlyTidePredictions", "HighLowTidePredictions"],
                    "description": "Optional value for data type"
                },   
                "datum": {   
                    "enum": [ "MLLW", "MSL", "MHW", "STND", "IGLD", "NAVD" ],
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
        return ['water_surface_height_above_reference_datum']
        
    def _getFeature(self, stationID):
        
        offeringid = 'station-%s' % stationID
    
        variables_list = []
    
        station = self.collectorCOOPS.server.contents[offeringid]
    
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
 
     
      