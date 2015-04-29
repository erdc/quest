from .base import DataServiceBase
import os
from geojson import Feature, FeatureCollection, Point
from datetime import date, datetime, timedelta
from .. import util
from pyoos.collectors.ndbc.ndbc_sos import NdbcSos

parameters_dict = {
        'air pressure': 'air_pressure_at_sea_level',
        'winds': 'winds',
    }

class NdbcPyoos(DataServiceBase):
    def register(self):
        """Register NDBC SOS plugin  
        """
    
        self.metadata = {
                    'provider': {
                                'abbr': 'NDBC',
                                'name': 'NOAA National Data Buoy Center (NDBC) SOS',                                 
                            },
                    'display_name': 'NOAA NDBC Sensor Observation Service',
                    'service': 'NOAA NDBC Sensor Observation Service',
                    'description': 'NOAA NDBC Sensor Obersvation Service',
                    'geographical area': 'Worldwide',
                    'bounding_boxes': [[-179.995, -77.466, 180.0, 80.81]], 
                    'geotype': 'points',
                    'datatype': 'timeseries' 
                }
                
    def get_locations(self, locations=None, bounding_box=None):
       
        try:
            
            if not hasattr(self, 'collectorNDBC'):
                self.collectorNDBC = NdbcSos()
            
            features = []            
            
            if locations:
                
                for location in locations:
                    features.append(self._getFeature(location))
                    
                return FeatureCollection(features)   
                
            else:
                  
                if bounding_box is None:
                    bounding_box = self.metadata['bounding_boxes'][0]                 
                
                xmin, ymin, xmax, ymax = [float(p) for p in bounding_box]
        
                for offeringID in self.collectorNDBC.server.contents.keys():
                    if not 'network' in offeringID:        
                        stationID = offeringID.split('-')[1]
                    
                        offeringid = 'station-%s' % stationID            
            
                        station = self.collectorNDBC.server.contents[offeringid]
            
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
        
    def get_data(self, locations, parameters=None, start_date=None, end_date=None, path=None):
      
        try:
            
            if not hasattr(self, 'collectorNDBC'):
                self.collectorNDBC = NdbcSos()
        
            ## come back for parameters check
            if parameters is None:
                parameters = self.provides()    
        
            times = [start_date, end_date]    
        
            if start_date is None and end_date is None:
                lastMonth_date = date.today() - timedelta(days=30)
                self.collectorNDBC.start_time = datetime.strptime(str(lastMonth_date), "%Y-%m-%d")
                self.collectorNDBC.end_time = datetime.strptime(str(date.today()), "%Y-%m-%d")
            elif any(time is None for time in times):
                 raise ValueError("must use either a date range with start/end OR use the default date")
            else:
                if start_date is not None:
                    # date is in Year-Month-Day format, (Ex: 2012-10-01)
                    self.collectorNDBC.start_time = datetime.strptime(start_date, "%Y-%m-%d")
            
                if end_date is not None:
                    self.collectorNDBC.end_time = datetime.strptime(end_date, "%Y-%m-%d")
                    
            if locations is None:
                raise ValueError("A location needs to be supplied.")
            
            if not path:
                path = util.get_dsl_dir()
                    
            if not os.path.exists(path):
                os.makedirs(path)
                    
            data_files = {}

            for location in locations:    
                
                print 'Location = %s' % location                
                
                data_files[location] = {}
                       
                self.collectorNDBC.features = [location]  #station id or network id                     
                
                for parameter in parameters:                

                    print 'Parameter = %s' % parameter

                    if (parameters_dict.has_key(parameter)):
                        
                        parameter_value = parameters_dict.get(parameter)                       

                        print 'parameter_value = %s' % parameter_value
                    
                        if (self._checkParameter(location, parameter_value)):                             
                
                            self.collectorNDBC.variables = [parameter_value]                    
                            
                            response = self.collectorNDBC.raw(responseFormat="text/csv")
        
                            filename = 'station-%s_%s.csv' % (location, parameter.replace(" ", ""))
                       
                           #write out a csv file for now but create a plugin to write out this data
                
                            csvFile_path = os.path.join(path, filename)

                            with open(csvFile_path, 'w') as f:
                                f.write(response)        
        
                            data_files[location][parameter] = filename        
                    else:
                         data_files[location][parameter] = 'None'   
                         
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
                "path": {
                    "type": "string",
                    "description": "base file path to store data"
                },
            },
            "required": ["locations", "variable"],
        }
        return schema
        
    def provides(self):
        return ['air pressure', 'winds']
        
    def _getFeature(self, stationID):
        
        offeringid = 'station-%s' % stationID
    
        variables_list = []
    
        station = self.collectorNDBC.server.contents[offeringid]
    
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
 
    def _checkParameter(self, stationID, parameter):

        offeringid = 'station-%s' % stationID

        station = self.collectorNDBC.server.contents[offeringid]
    
        parameterCheck = False      
    
        if any(parameter in op for op in station.observed_properties):    
            parameterCheck = True
        else: 
            parameterCheck = False
            
        return parameterCheck

    
    
  