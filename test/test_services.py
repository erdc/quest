import os
import pytest

from conftest import FILES_DIR

pytestmark = pytest.mark.usefixtures('reset_projects_dir')


def test_add_and_remove_provider(api):
    user_provider_path = os.path.join(FILES_DIR, 'user_provider')
    api.add_provider(user_provider_path)
    assert 'user-test-service' in api.get_providers()
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
    services = [
                 'svc://nasa:srtm-3-arc-second',
                 'svc://nasa:srtm-30-arc-second',
                 'svc://ncdc:ghcn-daily',
                 'svc://ncdc:gsod',
                 'svc://noaa:coops-meteorological',
                 'svc://noaa:coops-water',
                 'svc://noaa:ndbc',
                 'svc://usgs-ned:1-arc-second',
                 'svc://usgs-ned:13-arc-second',
                 'svc://usgs-ned:19-arc-second',
                 'svc://usgs-ned:alaska-2-arc-second',
                 'svc://usgs-nlcd:2001',
                 'svc://usgs-nlcd:2006',
                 'svc://usgs-nlcd:2011',
                 'svc://usgs-nwis:dv',
                 'svc://usgs-nwis:iv'
                ]

    assert api.get_services() == services
