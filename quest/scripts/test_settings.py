import quest


#
#
# quest.api.update_settings({'BASE_DIR':'/Users/rditllkw/QUEST/data-services-library/test/files'})
# quest.api.update_settings({'PROJECTS_DIR':'projects_template'})
quest.api.new_project('project1')
quest.api.new_project('project2')
quest.api.new_project('test_data')

quest.api.set_active_project('project1')
quest.api.new_collection('col1')
quest.api.new_collection('col2')
quest.api.new_collection('col3')


quest.api.set_active_project('test_data')
quest.api.new_collection('col1')
feature = quest.api.add_features('col1', 'svc://usgs-nwis:iv/01516350')
dataset = quest.api.stage_for_download(feature, download_options={'parameter': 'streamflow'})
quest.api.download_datasets(dataset)



