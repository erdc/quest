services = {
        'usgs-nwis-iv': 'dsl.services.usgs_nwis:NwisIv',
        'usgs-nwis-dv': 'dsl.services.usgs_nwis:NwisDv',
        #usgs-ned-1: dsl.services.usgs_ned:UsgsNed1ArcSecond
        #usgs-ned-13: dsl.services.usgs_ned:UsgsNed13ArcSecond
        #usgs-ned-19: dsl.services.usgs_ned:UsgsNed19ArcSecond
        #usgs-ned-2: dsl.services.usgs_ned:UsgsNed2ArcSecond
        #usgs-eros-nlcd2001: dsl.services.usgs_eros:UsgsErosNlcd2001
        #usgs-eros-nlcd2006: dsl.services.usgs_eros:UsgsErosNlcd2006
        #ncdc-ghcn: dsl.services.ncdc_ghcn:NcdcGhcn
        #ncdc-gsod: dsl.services.ncdc_gsod:NcdcGsod
        #example-points: dsl.services.example:ExamplePoints
        #example-polys: dsl.services.example:ExamplePolys
        #example-vitd: dsl.services.example:ExampleVITD
        #iraq-vitd: dsl.services.iraq_demo:IraqVITD
        #iraq-agc-tlidar: dsl.services.iraq_demo:IraqAGCTLidar
        #iraq-agc-alidar: dsl.services.iraq_demo:IraqAGCALidar
        #chesapeake-elevation: dsl.services.chesapeake_demo:ChesapeakeVTK
    }

filters = {
        'vitd-basic': 'dsl.filters.vitd:Basic',
    }

io = {
        'ts-geojson': 'dsl.io.ts_geojson:TsGeojson',
    }