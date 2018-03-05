import os
import pytest

from conftest import FILES_DIR

from data import ALL_SERVICES, SERVICE_FEATURE_DOWNLOAD_OPTIONS

test_download = pytest.mark.skipif(
    not pytest.config.getoption("--test-download"),
    reason="--test-download option was not set"
)

pytestmark = pytest.mark.usefixtures('reset_projects_dir')


def test_add_and_remove_provider(api):
    user_provider_path = os.path.join(FILES_DIR, 'user_provider')
    api.add_provider(user_provider_path)
    providers = api.get_providers()
    assert 'user-test-service' in providers
    assert 'svc://user-test-service:test' in api.get_services()

    api.delete_provider(user_provider_path)
    assert 'user-test-service' not in api.get_providers()
    assert 'svc://user-test-service:test' not in api.get_services()


def test_get_providers(api):
    path = os.path.join(FILES_DIR, '..', '..', 'setup.cfg')
    with open(path, 'r') as setup:
        counter = 0
        for n, line in enumerate(setup.readlines()):
            if 'quest.services.' in line:
                if '#' not in line and 'user' not in line:  # need to handle user defined providers separately
                    counter += 1
    providers = api.get_providers()
    assert counter == len(providers)


def test_get_services(api):
    assert sorted(api.get_services()) == ALL_SERVICES

@test_download
@pytest.mark.parametrize('feature, options', SERVICE_FEATURE_DOWNLOAD_OPTIONS)
def test_download(api, feature, options):
    api.new_collection('test')
    collection_feature = api.add_features('test', feature)
    d = api.stage_for_download(collection_feature, options=options)[0]
    result = api.download_datasets(d, raise_on_error=True)
    assert result[d] == 'downloaded'
