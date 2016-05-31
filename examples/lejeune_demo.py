"""Camp Lejeune demo script:

This script does the following:
    1. creates a collection called camp_lejeune
    2. adds sites to it from several dataservices
    3. download data for the sites
    4. apply some filters
    5. create plots 

note: sites were chosen visually in DataBrowser and by checking that they had recent data. 
"""
from __future__ import print_function
from builtins import input
import dsl
import datetime
import shutil
import os

######################################################################################################################
# create a lejeune demo collection:

collection_name = input('Enter Collection Name (default: camp_lejeune):')
save_path = input('Enter output path to save plots and adh exported data (default is $ENVSIM_DSL_DIR/adh):')
if save_path=='':
    save_path = os.path.join(dsl.util.get_dsl_dir(), 'adh')

dsl.util.mkdir_if_doesnt_exist(save_path)

if collection_name=='':
    collection_name = 'camp_lejeune'

print('creating collection %s' % collection_name)
dsl.api.new_collection(collection_name)

######################################################################################################################
# add sites to this location
print('adding sites to collection')

# ndbc
#ndbc=dsl.api.add_features(collection_name, "svc://noaa:ndbc/41036, svc://noaa:ndbc/41037")

# usgs nwis iv
usgs_nwis=dsl.api.add_features(collection_name, "svc://usgs-nwis:iv/02093000")

# coops
# dsl.api.add_features(collection_name, 'noaa-coops', '8658163')

# ned 1/9 arc second
usgs_ned=dsl.api.add_features(collection_name, "svc://usgs-ned:19-arc-second/53174dbde4b0cd4cd83c4421")

##Usgs-Ero-Nlcd2008 is not listed as a service
# # nlcd 2006
# #dsl.api.add_features(collection_name, "usgs-eros-nlcd2006", "L6N_2006/landcover/conus/NLCD2006_LC_N33W075_v1")

# ######################################################################################################################
# # download data (each site done individually since we are using non default download options)

images = {}
today = datetime.datetime.today()
start_30 = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
start_365 = (today - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
end = today.strftime('%Y-%m-%d')

# coops
# currently can only request 30 days for wind and air pressure
# dsl.api.download_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="tidal_elevation", start_date=start_365, end_date=end, data_type='VerifiedHourlyHeight')
# dsl.api.download_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="wind", start_date=start_30, end_date=end)
# dsl.api.download_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="air_pressure", start_date=start_30, end_date=end)
# images.update({
#     'noaa-coops-tides': dsl.api.view_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="tidal_elevation"),
#     'noaa-coops-wind': dsl.api.view_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="wind"),
#     'nooa-coops-airpressure': dsl.api.view_in_collection(collection_name, service="noaa-coops", location="8658163", parameter="air_pressure"),
#     })

# # usgs
usgs_nwis=dsl.api.stage_for_download(usgs_nwis,download_options={'parameter':'streamflow','period':'P1825D'})
#images.update({'usgs-streamflow': dsl.api.view_in_collection(collection_name, service="usgs-nwis-iv", location="02093000", parameter="streamflow")})

# ndbc THIS IS VERY FLAKY DISABLING
# thse downloads are a bit slow and limited to 30 day window. air_pressure returning no data even though data exists

#ndbc=dsl.api.stage_for_download(ndbc, download_options={'parameter':'wind', 'start_date':start_30, 'end_date':end})
#images.update({
#    'noaa-ndbc-wind-41036': dsl.api.view_in_collection(collection_name, service="noaa-coops", location="41036", parameter="wind"),
#    'noaa-ndbc-wind-41037': dsl.api.view_in_collection(collection_name, service="noaa-coops", location="41037", parameter="wind"),
#    })

# # raster sites (these might take a while)
usgs_ned=dsl.api.stage_for_download(usgs_ned, download_options={'parameters':'elevation'})
# # images.update({'usgs-ned-1/9arc-second': dsl.api.view_in_collection(collection_name, service="usgs-ned-19", location="53174dbde4b0cd4cd83c4421", parameter="elevation")})

# # # usgs landcover service is not working on usgs side
# # #dsl.api.download_in_collection(collection_name, service="usgs-eros-nlcd2006", location="L6N_2006/landcover/conus/NLCD2006_LC_N33W075_v1", parameter="landcover")
print('~~~~~~~~~~Downloading data for usgs_nwis~~~~~~~~~~~')
stat_nwis=dsl.api.download_datasets(usgs_nwis)
print('~~~~~~~~~~Downloading data for usgs_ned~~~~~~~~~~~')
#stat_ned=dsl.api.download_datasets(usgs_ned)

# # ######################################################################################################################
# # # apply some filters
print('~~~~~~~~~~Applying filters to usgs_nwis~~~~~~~~~~~')
# # # remove crazy spike from usgs data
new_usgs=dsl.api.apply_filter('ts-remove-outliers',datasets=usgs_nwis)
images.update({'usgs-streamflow-outliers-removed':dsl.api.visualize_dataset(new_usgs.keys()[0])})

# # # demo calculating monthly max streamflow
new1_usgs=dsl.api.apply_filter('ts-resample', datasets=usgs_nwis, options={'period':'weekly', 'method':'mean'})
images.update({'usgs-streamflow-outliers-removed-monthly-max':dsl.api.visualize_dataset(new1_usgs.keys()[0])})


##uncomment when ToAdh is implemented 
# # # export clean data to adh after clipping to 1 year ago
#dsl.api.apply_filter('ts-2-adh', collection_name=collection_name, service="local", location="02093000", parameter="streamflow (outliers removed)", start_time=start_365, export_path=save_path, filename='usgs_streamflow')
# # dsl.api.apply_filter('ts-2-adh', collection_name=collection_name, service="noaa-coops", location="8658163", parameter="tidal_elevation", start_time=start_365, export_path=save_path, filename='noaa_tides')

##uncomment when ExportRaster is implemented 
# # # export ned 1/9 arc second to USGSDEM format
#dsl.api.apply_filter('export-raster',datasets=usgs_ned, options={'export_path':save_path, 'filename':'usgs_ned', 'fmt':'USGSDEM'})

print('copying image files to %s' % save_path)
for name, path in images.items():
    print('copying %s: %s' % (name, path))
    shutil.copy(path, save_path)
