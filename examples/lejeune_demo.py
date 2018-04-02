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
import quest
import datetime
import shutil
import os

######################################################################################################################
# create a lejeune demo collection:

collection_name = input('Enter Collection Name (default: camp_lejeune):')
save_path = input('Enter output path to save plots and adh exported data (default is $QUEST_DIR/adh):')
if save_path=='':
    save_path = os.path.join(quest.util.get_quest_dir(), 'adh')

quest.util.mkdir_if_doesnt_exist(save_path)

if collection_name=='':
    if 'camp_lejeune' in quest.api.get_collections():
        collection_name=input('A collection named "camp_lejeune" already exists. Enter another collection name ')
    else:
         collection_name = 'camp_lejeune'

print('creating collection %s' % collection_name)
quest.api.new_collection(collection_name)

######################################################################################################################
# add sites to this location
print('adding sites to collection')

# usgs nwis iv
usgs_nwis=quest.api.add_features(collection_name, 'svc://usgs-nwis:iv/02093000')

# ned 1/9 arc second
usgs_ned=quest.api.add_features(collection_name,'svc://usgs-ned:19-arc-second/581d2561e4b08da350d5a3b2')

# ######################################################################################################################
# # download data (each site done individually since we are using non default download options)

images = {}
today = datetime.datetime.today()
start_30 = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
start_365 = (today - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
end = today.strftime('%Y-%m-%d')

# # usgs
usgs_nwis=quest.api.stage_for_download(usgs_nwis, options={'parameter':'streamflow','period':'P1825D'})

# # raster sites (these might take a while)
usgs_ned=quest.api.stage_for_download(usgs_ned, options={'parameters':'elevation'})

# # # usgs landcover service is not working on usgs side
print('~~~~~~~~~~Downloading data for usgs_nwis~~~~~~~~~~~')
stat_nwis=quest.api.download_datasets(usgs_nwis)
print('~~~~~~~~~~Downloading data for usgs_ned~~~~~~~~~~~')
stat_ned=quest.api.download_datasets(usgs_ned)

# # ######################################################################################################################
# # # apply some filters
print('~~~~~~~~~~Applying filters to usgs_nwis~~~~~~~~~~~')
# # # remove crazy spike from usgs data
new_usgs=quest.api.apply_filter('ts-remove-outliers',datasets=usgs_nwis)
images.update({'usgs-streamflow-outliers-removed':quest.api.visualize_dataset(new_usgs['datasets'][0])})

# # # # demo calculating monthly max streamflow
new1_usgs=quest.api.apply_filter('ts-resample', datasets=usgs_nwis, options={'period':'weekly', 'method':'mean'})
images.update({'usgs-streamflow-outliers-removed-monthly-max':quest.api.visualize_dataset(new_usgs['datasets'][0])})


print('copying image files to %s' % save_path)
for name, path in images.items():
    print('copying %s: %s' % (name, path))
    shutil.copy(path, save_path)

