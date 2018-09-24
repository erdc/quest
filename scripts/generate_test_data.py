"""This generates test data for Quest tests."""
import os
import shutil
import quest

TEST_PATH = '../../test/files/'
PROJECT_DIR = 'projects_template'
START_DATE = '2018-08-15 12:00:00'
END_DATE = '2018-09-15 12:00:00'

try:
    shutil.rmtree(os.path.join(TEST_PATH, PROJECT_DIR))
except:
    pass

quest.api.update_settings({'BASE_DIR': TEST_PATH, 'PROJECTS_DIR': PROJECT_DIR})
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
quest.api.stage_for_download(datasets, options={'parameter': 'streamflow', 'start': START_DATE, 'end': END_DATE})
quest.api.download_datasets(datasets)
print('The new test data dataset name is {}. Make sure to update this in test/data.py'.format(datasets[0]))


