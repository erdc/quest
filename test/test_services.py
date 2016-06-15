import dsl
import os


def test_get_providers():
    path= os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))+'/setup.cfg'
    setup=open(path,'r')
    counter=0
    for n,line in enumerate(setup.readlines()):
        if 'dsl.services.' in line:
            if '#' not in line:
                counter += 1
    assert counter==len(dsl.api.get_providers())


def test_get_services():
    services = [
        'svc://nasa:srtm-3-arc-second',
        'svc://nasa:srtm-30-arc-second',
        'svc://ncdc:ghcn-daily',
        'svc://ncdc:gsod',
        'svc://noaa:coops',
        'svc://noaa:ndbc',
        'svc://usgs-ned:1-arc-second',
        'svc://usgs-ned:13-arc-second',
        'svc://usgs-ned:19-arc-second',
        'svc://usgs-ned:alaska-2-arc-second',
        'svc://usgs-nlcd:2001',
        'svc://usgs-nlcd:2006',
        'svc://usgs-nlcd:2011',
        'svc://usgs-nwis:dv',
        'svc://usgs-nwis:iv']
    assert dsl.api.get_services()==services


