"""basic example of quest api functionality
"""
import os

import quest


def _get_available_parameters(parameters):
    """helper function to extract a parameter list from the result of quest.api.get_parameters
    """
    if isinstance(parameters, dict):
        available_parameters = parameters['parameters']
    else:  # if parameters is a DataFrame
        available_parameters = set(parameters['parameter'])
        if available_parameters:
            available_parameters.discard(None)
        available_parameters = list(available_parameters)
    return available_parameters

# get list of available providers
services = quest.api.get_services()

# make a dict so we can refer to each service by a number rather than service code
svc_dict = {k: v for k, v in enumerate(services)}

print('%s QUEST providers are available:' % len(services))
for n, service in enumerate(services):
    parameters = quest.api.get_parameters(svc_dict[n])
    available_parameters = _get_available_parameters(parameters)
    print("\t%s - %s, (provides %s)" % (n, service, available_parameters))


chosen_services = input('Choose providers to use (comma separated numbers or hit Enter for all):')
if not chosen_services:
    chosen_services = list(svc_dict.keys())
    print('\tUsing all providers')
else:
    chosen_services = [int(n) for n in chosen_services.split(',')]

# get available features
bounding_box = input('Enter a bounding box (lon_min, lat_min, lon_max, lat_max) OR Press Enter to use default:')

if not bounding_box:
    bounding_box = '-98.173286,30.023451,-97.369926,30.62817'
    print('\tUsing default bounding box Travis County (Austin): %s' % bounding_box)

bounding_box = [float(p) for p in bounding_box.split(',')]

features = {}
for svc in chosen_services:
    print('Getting feature data for service: ', svc_dict[svc])
    features[svc] = quest.api.get_features(svc_dict[svc], filters={'bbox': bounding_box})
    print('\n~~~~~~~ %s features retrieved for%s ~~~~~~~~\n' % (len(features[svc]), svc_dict[svc]))

print('Features Retrieved:')
for svc in chosen_services:
    print('\t%s - %s  -> %s features retrieved' % (svc, svc_dict[svc], len(features[svc])))

# get the project path
project_path = quest.api.get_projects(as_dataframe=True)['folder'][quest.api.get_active_project()]


collections = quest.api.get_collections()
print('Available Collections:')
print('~~~~~~~~~~~~~~~~~~~~~~')
for name in collections:
    print('%s - path:%s' % (name, os.path.join(project_path, name)))
print('~~~~~~~~~~~~~~~~~~~~~~')
collection_name = input('Type collection name to use (will be created if it is not in list above, '
                        'default is no collection):')
if collection_name and collection_name not in collections:
    quest.api.new_collection(collection_name)
    col = quest.api.get_collections(collection_name)
    print('collection created at %s' % os.path.join(project_path, collection_name))
# collections = quest.api.get_collections(metadata=True)

print('~~~adding first 2 features from each chosen service to collection~~~\n')

for svc in chosen_services:
    feats = [p for p in features[svc][:2]]
    if len(feats) == 0:
        print('No features available for ', svc_dict[svc])
        continue
    feats = ','.join(feats)  # convert from list to csv
    print('~~~Adding features [%s] from %s~~~\n' % (feats, svc_dict[svc]))
    feats = quest.api.add_features(collection_name, feats)

    print('Available parameter(s) for %s\n' % (svc_dict[svc]))
    parameters = quest.api.get_parameters(svc_dict[svc])
    available_parameters = _get_available_parameters(parameters)
    if available_parameters:
        for number, param in enumerate(available_parameters):
            print(number, ':', param)

        chosen_parameters = input('\nChoose which parameter(s) to download (comma separated numbers or hit Enter for all):')
        if not chosen_parameters:
            chosen_parameters = available_parameters
            print('\tUsing all parameters')
        else:
            try:
                chosen_parameters = [available_parameters[int(c)] for c in chosen_parameters.split(',')]
            except IndexError:
                print('Not an available parameter.\n')

        datasets = []
        for parameter in chosen_parameters:
            datasets.extend(quest.api.stage_for_download(feats, options={'parameter': parameter}))
        print('\n~~~Downloading data for chosen parameters~~~\n')
        try:
            stat = quest.api.download_datasets(datasets=datasets, raise_on_error=True)
        except ValueError as e:
            print(e)
    else:
        print('No parameters available for ', svc_dict[svc])
