"""This generates test data for Quest tests."""
import os
import shutil
import quest

test_path = '../../test/files/'
project_dir = 'projects_template'

try:
    shutil.rmtree(os.path.join(test_path, project_dir))
except:
    pass

quest.api.update_settings({'BASE_DIR': test_path, 'PROJECTS_DIR': project_dir})
quest.api.new_project('project1')
quest.api.new_project('project2')
quest.api.new_project('test_data')

quest.api.set_active_project('project1')
quest.api.new_collection('col1')
quest.api.new_collection('col2')
quest.api.new_collection('col3')


quest.api.set_active_project('test_data')
quest.api.new_collection('col1')
datasets = quest.api.add_datasets('col1', 'svc://usgs-nwis:iv/01516350')
dataset = quest.api.stage_for_download(datasets, options={'parameter': 'streamflow'})
quest.api.download_datasets(dataset)



