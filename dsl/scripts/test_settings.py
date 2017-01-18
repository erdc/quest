import dsl


#
#
# dsl.api.update_settings({'BASE_DIR':'/Users/rditllkw/DSL/data-services-library/test/files'})
# dsl.api.update_settings({'PROJECTS_DIR':'projects_template'})
dsl.api.new_project('project1')
dsl.api.new_project('project2')
dsl.api.new_project('test_data')

dsl.api.set_active_project('project1')
dsl.api.new_collection('col1')
dsl.api.new_collection('col2')
dsl.api.new_collection('col3')


dsl.api.set_active_project('test_data')
dsl.api.new_collection('col1')
feature = dsl.api.add_features('col1', 'svc://usgs-nwis:iv/01516350')
dataset = dsl.api.stage_for_download(feature, download_options={'parameter': 'streamflow'})
dsl.api.download_datasets(dataset)



