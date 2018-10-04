import os

import pytest

from conftest import FILES_DIR
from quest.static import DatasetStatus
from data import ALL_SERVICES, SERVICE_DOWNLOAD_OPTIONS



pytestmark = pytest.mark.usefixtures('reset_projects_dir')


def test_add_and_remove_provider(api):
    user_provider_path = os.path.join(FILES_DIR, 'user_provider')
    api.add_user_provider(user_provider_path)
    providers = api.get_providers()
    assert 'user-test-service' in providers
    assert 'svc://user-test-service:test' in api.get_services()

    api.delete_user_provider(user_provider_path)
    assert 'user-test-service'  not in api.get_providers()
    assert 'svc://user-test-service:test' not in api.get_services()


def test_get_providers(api):
    actual = len(api.get_providers())
    assert actual > 0


def test_get_services(api):
    assert sorted(api.get_services()) == ALL_SERVICES


@pytest.mark.download
@pytest.mark.parametrize('catalog_entry, options', SERVICE_DOWNLOAD_OPTIONS)
def test_download(api, catalog_entry, options):
    api.new_collection('test')
    d = api.add_datasets('test', catalog_entry)[0]
    api.stage_for_download(d, options=options)
    result = api.download_datasets(d, raise_on_error=True)
    assert result[d] == DatasetStatus.DOWNLOADED
