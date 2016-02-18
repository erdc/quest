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
from __future__ import print_function
import dsl

bbox = []

cid = 'gssha-test'
dsl.api.new_collection(cid)
services = ['service://usgs-ned::1-arc-second']
filters = {'parameter': 'elevation', 'bbox': bbox}
features = dsl.api.get_features(services, filters=filters)
features = dsl.api.add_to_collection(cid, features) 
elevation_rasters = dsl.api.stage_for_download(features, options={'parameter': 'elevation'})

services = ['service://usgs-nlcd::2006']
filters = {'parameter': 'landcover' , 'bbox': bbox}
features = dsl.api.get_features(services, filters=filters)
features = dsl.api.add_to_collection(cid, features)
landcover_rasters = dsl.api.stage_for_download(features, options={'parameter': 'landcover'})

# dsl.api.download_options(elevation_rasters))
dsl.api.download(elevation_rasters)

reprojected_rasters = dsl.api.apply_filter('raster-reproject', elevation_rasters, options={'target_projection': 'UTM15'})
merged_raster = dsl.api.apply_filter('raster-merge-clip', reprojected_rasters, options={})
pit_removed = dsl.api.apply_filter('pit-remove', merged_raster)
flow_dir_grid = dsl.api.apply_filter('dinf-flow-dir', pit_removed)
flow_accumulation = dsl.api.apply_filter('flow-accum', flow_grid=flow_dir_grid, elevation_raster=pit_removed)
approx_outlet = dsl.api.new_feature(cid, geom_type='Point', geom_coord=[-94.3, 34.5], display_name='Approx Outlet Position')
outlet, watershed_boundary, stream_network = dsl.apply_filter('watershed-delineation', outlet=approx_outlet, elevation_raster=pit_removed, threshold=3)

dsl.api.download(landcover_rasters)
reprojected_rasters = dsl.api.apply_filter('raster-reproject', landcover_rasters, options={'target_projection': 'UTM15'})
input_grids = dsl.api.apply_filter('gssha-landcover-inputgrid', reprojected_rasters, grid_cell_size=25)
