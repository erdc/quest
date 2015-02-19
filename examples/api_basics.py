"""basic example of dsl api functionality
"""

import dsl

#get list of available services
services = dsl.api.get_services()

#make a dict so we can refer to each service by a number rather than service code
svc_dict = {k:v['service_code'] for k,v in enumerate(services)}

print '%s DSL services are available:' % len(services)
for n, service in enumerate(services):
    available_parameters = dsl.api.get_parameters(svc_dict[n])
    print "\t%s - %s, (provides %s)" % (n, service['display_name'], available_parameters)


chosen_services = raw_input('Choose services to use (comma separated numbers or hit Enter for all):')
if not chosen_services:
    chosen_services = svc_dict.keys()
    print '\tUsing all services'
else:
    chosen_services = [int(n) for n in chosen_services.split(',')]

#get available locations
bounding_box = raw_input('Enter a bounding box (lon_min, lat_min, lon_max, lat_max) OR Press Enter to use default:')

if not bounding_box:
    bounding_box = '-98.173286,30.023451,-97.369926,30.62817'
    print '\tUsing default bounding box Travis County (Austin): %s' % bounding_box

bounding_box = [float(p) for p in bounding_box.split(',')]

locations = {}
for svc in chosen_services:
    print 'Getting location data for service: ', svc_dict[svc]
    locations[svc] = dsl.api.get_locations(svc_dict[svc], bounding_box=bounding_box)
    print '\n~~~~~~~ %s locations retrieved for %s ~~~~~~~~\n' % (len(locations[svc]['features']), svc_dict[svc])

print 'Locations Retrieved:'
for svc in chosen_services:
    print '\t%s - %s  -> %s locations retrieved' % (svc, svc_dict[svc], len(locations[svc]['features']))

collections = dsl.api.list_collections()
print 'Available Collections:'
print '~~~~~~~~~~~~~~~~~~~~~~'
for name, metadata in collections.iteritems():
    print '%s - path:%s' % (name, metadata['path'])
print '~~~~~~~~~~~~~~~~~~~~~~'
collection_name = raw_input('Type collection name to use (will be created if it is not in list above:')
if collection_name not in collections.keys():
    dsl.api.new_collection(collection_name)
    col = dsl.api.get_collection(collection_name)
    print 'collection created at %s' % col['path']

print '~~~adding first 2 locations (all parameters) from each chosen service to collection~~~'

for svc in chosen_services:
    locs = [p['id'] for p in locations[svc]['features'][:2]]
    if len(locs)==0:
        print 'No locations available for ', svc_dict[svc]
        continue
    locs = ','.join(locs) # convert from list to csv
    print '\t adding locs: [%s] from %s' % (locs, svc_dict[svc])
    dsl.api.add_to_collection(collection_name, svc_dict[svc],locs)

print '~~~downloading data for all available parameters~~~'
collection = dsl.api.download_in_collection(collection_name)

print '~~~Data has been downloaded to :%s~~~' % collection['path']
print '~~~Metadata and location data will be in the file dsl_metadata.json~~~'
