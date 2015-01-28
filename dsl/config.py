source_dict = [
    {
        'name': 'USGS NWIS Web Services',
        'source': 'United States Geological Survey (USGS)',
        'services': [
                {
                    'uid' : 'usgs-nwis-iv',
                    'name': 'instantaneous values service',
                    'description': 'instantaneous values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries' 
                },
                {
                    'uid' : 'usgs-nwis-dv',
                    'name': 'instantaneous values',
                    'description': 'daily values at USGS monitoring locations',
                    'geographical area': 'USA',
                    'geotype': 'points',
                    'type': 'timeseries' 
                },
            ],
    },
    {
        'name': 'NCDC Services',
        'source': 'National Climatic Data Center (NCDC)',
        'services': [
                {
                    'uid' : 'ncdc-ghcn',
                    'name': 'Global Historic Climate Network service',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                },
                {
                    'uid' : 'ncdc-gsod',
                    'name': 'Global Summary of the Day',
                    'description': 'meteorological',
                    'geographical area': 'Worldwide',
                    'geotype': 'points',
                    'type': 'timeseries' 
                },
                {
                    'uid' : 'ncdc-cirs',
                    'name': 'Climate Index Reference Sequential',
                    'description': 'drought indices',
                    'geographical area': 'USA',
                    'geotype': 'polygons',
                    'type': 'timeseries' 
                }
            ],

    },
    {
        'name': 'USGS EROS Services',
        'source': 'United States Geological Survey (USGS)',
        'services': [
                {
                    'uid' : 'ncdc-eros-nlcd',
                    'name': 'National Land Cover Dataset',
                    'description': 'landcover',
                    'geographical area': 'USA',
                    'geotype': 'raster',
                    'type': 'categorical' 
                },
                {
                    'uid' : 'ncdc-color-ortho',
                    'name': 'Hi Resolution Color Ortho Imagery',
                    'description': 'imagery',
                    'geographical area': 'USA??',
                    'geotype': 'raster',
                    'type': 'imagery' 
                },
            ],
    },
    {
        'name': 'Fake NHD River Network Services',
        'source': 'National Hydrography Dataset (NHD)',
        'services': [
                {
                    'uid' : 'nhd-v1',
                    'name': 'NHD version 1',
                    'description': 'river networks',
                    'geographical area': 'USA',
                    'geotype': 'lines',
                    'type': 'network' 
                },
            ],
    },
]


def available_services():
    return source_dict