"""
Central location for all hard coded data needed for tests.
"""

DOWNLOAD_OPTIONS_FROM_ALL_SERVICES = {

    'svc://cuahsi-hydroshare:hs_geo': {},
    'svc://cuahsi-hydroshare:hs_norm': {},

}


SERVICES_FEATURE_COUNT = [

]


CACHED_SERVICES = [s[0] for s in SERVICES_FEATURE_COUNT]

ALL_SERVICES = sorted(DOWNLOAD_OPTIONS_FROM_ALL_SERVICES.keys())

SERVICE = 'svc://usgs-nwis:iv'
FEATURE = 'f92ad0e35d04402ab1b1d4621b48a636'
DATASET = 'df5c3df3229441fa9c779443f03635e7'

DATASET_METADATA = {

}

SERVICE_FEATURE_DOWNLOAD_OPTIONS = [

]
