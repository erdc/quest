"""Workflow example - GSSHA model setup.

1. Define region of interest
2. Get elevation raster tiles for region of interest (raster/scalar).
2a. Reproject
2b. Merge and clip
3. Applies filter(s) to generate flow-direction and accumulation grids.
4. Display options: vector/glyph plots, color map, and/or contour plots
5. Creates point feature to specify the approximate outlet position.
6. Applies filter(s) to generate watershed boundary and stream network
7. Get land cover data for region of interest (raster/category).
8. Applies filter(s) to generate GSSHA input grids.
9. User specifies parameters such as grid-cell size and precipitation in popup panel (standard filter arguments).
"""
import quest

# bounding box for Camp Lejeune
bbox = '-77.976387, 33.477428, -76.126134, 35.081018'

cname = 'gssha-test'
if cname not in quest.api.get_collections():
    quest.api.new_collection(cname)

# we do not need to specify parameter or download options for elevation
# or landcover data since the providers are single parameter,
# single file downloads
services = ['svc://usgs-ned:1-arc-second']
filters = {'bbox': bbox}
catalog_entries = quest.api.search_catalog(services, filters=filters)
datasets = quest.api.add_datasets(cname, catalog_entries)
elevation_rasters = quest.api.stage_for_download(datasets)


services = ['svc://usgs-nlcd:2006']
catalog_entries = quest.api.search_catalog(services, filters=filters)
datasets = quest.api.add_datasets(cname, catalog_entries)
landcover_rasters = quest.api.stage_for_download(datasets)

status = quest.api.download_datasets(elevation_rasters+landcover_rasters)

####################################
# NOT WORKING YET BELOW THIS COMMENT
#
# reprojected_rasters = quest.api.apply_filter('raster-reproject', elevation_rasters, options={'target_projection': 'UTM15'})
# merged_raster = quest.api.apply_filter('raster-merge-clip', reprojected_rasters, options={})
# pit_removed = quest.api.apply_filter('pit-remove', merged_raster)
# flow_dir_grid = quest.api.apply_filter('dinf-flow-dir', pit_removed)
# flow_accumulation = quest.api.apply_filter('flow-accum', flow_grid=flow_dir_grid, elevation_raster=pit_removed)
# approx_outlet = quest.api.new_feature(cid, geom_type='Point', geom_coord=[-94.3, 34.5], display_name='Approx Outlet Position')
# outlet, watershed_boundary, stream_network = quest.apply_filter('watershed-delineation', outlet=approx_outlet, elevation_raster=pit_removed, threshold=3)
#
# quest.api.download(landcover_rasters)
# reprojected_rasters = quest.api.apply_filter('raster-reproject', landcover_rasters, options={'target_projection': 'UTM15'})
# input_grids = quest.api.apply_filter('gssha-landcover-inputgrid', reprojected_rasters, grid_cell_size=25)
