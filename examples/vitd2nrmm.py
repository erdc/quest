"""basic example of vitd 2 nrmm conversion

Note: some things are hardwired and no actual call to the C++ code is made. DSL just sleeps for 10 seconds
"""

import dsl


print '~~~ Downloading Iraq VITD locations ~~~'
locs = dsl.api.services.get_locations('iraq-vitd')
print '~~~ %s locations found' % len(locs['features'])

print 'Choose start location index and number of locations to add to collection'
print '(default is first 5 - i.e. 0,5)'
vals  = raw_input('start index, # of locations: ')
if vals=='':
    start, nlocs = 0, 5
else:
    start, nlocs = [int(n) for n in vals.split(',')]

locations = [f['id'] for f in locs['features'][start:start+nlocs]]
print 'Locations chosen: %s' % (', '.join(locations))

print 'Available collections:\n%s' % ('\n'.join(dsl.api.list_collections().keys()))

collection = raw_input('Enter collection name to add vitd chosen location (will be created if not above):')

if collection not in dsl.api.list_collections().keys():
    dsl.api.new_collection(collection)
    print '~~~ created collection: %s ~~~' % collection

print '~~~ adding locations to collection ~~~'
dsl.api.add_to_collection(collection, 'iraq-vitd', locations)

print '~~~ downloading data to collection ~~~'
dsl.api.download_in_collection(collection)

print '~~~ getting available filters ~~~'
print dsl.api.get_filters()

print '~~~ getting filter options ~~~'
for k,v in sorted(dsl.api.apply_filter_options('vitd2nrmm')['properties'].iteritems()):
    if k!='collection_name':
        print '%s: %s (type:%s)' % (k, v['description'], v['type'])

choices = raw_input('Enter comma separated list of themes i.e. obs,sdr (if left blank all will be used)')

if choices=='':
    dsl.api.apply_filter('vitd2nrmm', collection_name=collection)
else:
    kwargs = dict.fromkeys(choices.lower().split(','), True)
    dsl.api.apply_filter('vitd2nrmm', collection_name=collection, **kwargs)

print '~~~ processing complete ~~~'
print '~~~ see "local" dataset inside collection: %s ~~~' % collection


