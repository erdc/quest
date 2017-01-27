"""basic example of vitd 2 nrmm conversion

Note: some things are hardwired and no actual call to the C++ code is made. QUEST just sleeps for 10 seconds
"""
from __future__ import print_function
from builtins import input

import quest


print('~~~ Downloading Iraq VITD locations ~~~')
locs = quest.api.services.get_locations('iraq-vitd')
print('~~~ %s locations found' % len(locs['features']))

print('Choose start location index and number of locations to add to collection')
print('(default is first 5 - i.e. 0,5)')
vals  = input('start index, # of locations: ')
if vals=='':
    start, nlocs = 0, 5
else:
    start, nlocs = [int(n) for n in vals.split(',')]

locations = [f['id'] for f in locs['features'][start:start+nlocs]]
print('Locations chosen: %s' % (', '.join(locations)))

print('Available collections:\n%s' % ('\n'.join(list(quest.api.list_collections().keys()))))

collection = input('Enter collection name to add vitd chosen location (will be created if not above):')

if collection not in list(quest.api.list_collections().keys()):
    quest.api.new_collection(collection)
    print('~~~ created collection: %s ~~~' % collection)

print('~~~ adding locations to collection ~~~')
quest.api.add_to_collection(collection, 'iraq-vitd', locations)

print('~~~ downloading data to collection ~~~')
quest.api.download_in_collection(collection)

print('~~~ getting available filters ~~~')
print(quest.api.get_filters())

print('~~~ getting filter options ~~~')
for k,v in sorted(quest.api.apply_filter_options('vitd2nrmm')['properties'].items()):
    if k!='collection_name':
        print('%s: %s (type:%s)' % (k, v['description'], v['type']))

choices = input('Enter comma separated list of themes i.e. obs,sdr (if left blank all will be used)')

if choices=='':
    quest.api.apply_filter('vitd2nrmm', collection_name=collection)
else:
    kwargs = dict.fromkeys(choices.lower().split(','), True)
    quest.api.apply_filter('vitd2nrmm', collection_name=collection, **kwargs)

print('~~~ processing complete ~~~')
print('~~~ see "local" dataset inside collection: %s ~~~' % collection)


