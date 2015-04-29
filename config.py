services = {
        'usgs-nwis-iv': 'dsl.services.usgs_nwis:NwisIv',
        'usgs-nwis-dv': 'dsl.services.usgs_nwis:NwisDv',
        'usgs-ned-1': 'dsl.services.usgs_ned:UsgsNed1ArcSecond',
        'usgs-ned-13': 'dsl.services.usgs_ned:UsgsNed13ArcSecond',
        'usgs-ned-19': 'dsl.services.usgs_ned:UsgsNed19ArcSecond',
        'usgs-ned-2': 'dsl.services.usgs_ned:UsgsNed2ArcSecond',
        'usgs-eros-nlcd2001': 'dsl.services.usgs_eros:UsgsErosNlcd2001',
        'usgs-eros-nlcd2006': 'dsl.services.usgs_eros:UsgsErosNlcd2006',
        'iraq-vitd': 'dsl.services.iraq_demo:IraqVitd',
        'iraq-srtm': 'dsl.services.iraq_demo:IraqSrtm',
        'coops-pyoos': 'dsl.services.coops_pyoos:CoopsPyoos',
        'lejeune-precip': 'dsl.services.lejeune_demo:LejeuneGhcn',
        'local': 'dsl.services.local:LocalService',
        'ndbc-pyoos': 'dsl.services.ndbc_pyoos:NdbcPyoos',
        #iraq-agc-tlidar: dsl.services.iraq_demo:IraqAGCTLidar
        #iraq-agc-alidar: dsl.services.iraq_demo:IraqAGCALidar
        #chesapeake-elevation: dsl.services.chesapeake_demo:ChesapeakeVTK
    }

filters = {
        'vitd2nrmm': 'dsl.filters.nrmm:NrmmFromVITD',
    }

io = {
        'ts-geojson': 'dsl.io.ts_geojson:TsGeojson',
    }