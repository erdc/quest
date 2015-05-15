services = {
        'local': 'dsl.services.local:LocalService',
        'usgs-nwis-iv': 'dsl.services.usgs_nwis:NwisIv',
        'usgs-nwis-dv': 'dsl.services.usgs_nwis:NwisDv',
        'usgs-ned-1': 'dsl.services.usgs_ned:UsgsNed1ArcSecond',
        'usgs-ned-13': 'dsl.services.usgs_ned:UsgsNed13ArcSecond',
        'usgs-ned-19': 'dsl.services.usgs_ned:UsgsNed19ArcSecond',
        'usgs-ned-2': 'dsl.services.usgs_ned:UsgsNed2ArcSecond',
        'usgs-eros-nlcd2001': 'dsl.services.usgs_eros:UsgsErosNlcd2001',
        'usgs-eros-nlcd2006': 'dsl.services.usgs_eros:UsgsErosNlcd2006',
        'noaa-coops': 'dsl.services.coops_pyoos:CoopsPyoos',
        'noaa-ndbc': 'dsl.services.ndbc_pyoos:NdbcPyoos',
    }

filters = {
        'vitd2nrmm': 'dsl.filters.nrmm:NrmmFromVITD',
        'ts-resample': 'dsl.filters.timeseries:TsResample',
        'ts-remove-outliers': 'dsl.filters.timeseries:TsRemoveOutliers',
        'ts-2-adh': 'dsl.filters.timeseries:ToAdh',
        'export-raster': 'dsl.filters.export_raster:ExportRaster',
    }

io = {
        'ts-geojson': 'dsl.io.ts_geojson:TsGeojson',
        'vitd': 'dsl.io.vitd:Vitd',
        'generic': 'dsl.io.generic:Generic',
    }