import os

import numpy as np
import param

from quest.plugins import ToolBase
from quest import util
from quest.api import get_metadata, new_dataset, update_metadata, open_dataset
from quest.api.projects import active_db

from .whitebox_utils import wbt, points_to_shp, raster_to_polygons


class WBTFillDepressions(ToolBase):
    _name = 'wbt-fill-depressions'

    # metadata attributes
    group = 'raster'
    operates_on_datatype = ['raster']
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = ['raster']
    produces_geotype = None
    produces_parameters = None

    dataset = util.param.DatasetSelector(
        default=None,
        doc="""Dataset to run tool on.""",
        filters={'datatype': 'raster'},
    )

    def _run_tool(self):
        dataset = self.dataset

        orig_metadata = get_metadata(dataset)[dataset]
        collection_name = orig_metadata['collection']
        elev_file = orig_metadata['file_path']

        new_dset = new_dataset(
            feature=orig_metadata['feature'],
            source='derived',
            # display_name=self.display_name,
            description=self.description
        )

        self.set_display_name(new_dset)
        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        self.file_path = os.path.join(dst, new_dset + '.tiff')

        wbt.fill_depressions(elev_file, output=self.file_path)

        quest_metadata = {
            'parameter': 'streams',
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata)

        return {'datasets': new_dset}


class WBTExtractStreamsWorkflow(ToolBase):
    """Whitebox_tools workflow to extract a stream network from a filled elevation raster.
    """
    _name = 'wbt-extract-streams-workflow'

    # metadata attributes
    group = 'raster'
    operates_on_datatype = ['raster']
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = ['raster']
    produces_geotype = None
    produces_parameters = None

    dataset = util.param.DatasetSelector(
        default=None,
        doc="""Dataset to run tool on.""",
        filters={'datatype': 'raster'},
    )

    stream_threshold = param.Number(
        default=1,
        bounds=(0,1000),  # TODO is there a way to not have an upper bound?
        doc="""stream threshold specified as an absolute value"""
    )

    flow_accumulation = None

    def set_threshold_bounds(cls):
        if cls.dataset:
            orig_metadata = get_metadata(cls.dataset)[cls.dataset]
            elev_file = orig_metadata['file_path']
            fa = cls.flow_accumulation = wbt.d_inf_flow_accumulation(elev_file)
            amax = np.nanmax(fa) * .5
            amin = np.nanmean(fa)
            threshold = cls.params()['stream_threshold']
            threshold.bounds = (amin, amax)
            threshold.default = amax * 0.1



    # algorithm = param.ObjectSelector(default="go-fill",
    #                                  doc="""algorithm to use for filling the dem""",
    #                                  objects=list(FILL_ALGORITHMS.keys()),
    #                                  )

    def _run_tool(self):
        dataset = self.dataset

        # get metadata, path etc from dataset

        orig_metadata = get_metadata(dataset)[dataset]
        collection_name = orig_metadata['collection']
        elev_file = orig_metadata['file_path']

        new_dset = new_dataset(
            feature=orig_metadata['feature'],
            source='derived',
            # display_name=self.display_name,
            description=self.description
        )

        self.set_display_name(new_dset)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        self.file_path = os.path.join(dst, new_dset + '.tiff')

        fa = self.flow_accumulation if self.flow_accumulation is not None else wbt.d_inf_flow_accumulation(elev_file)
        # fa = wbt.d8_flow_accumulation(fill)
        wbt.extract_streams(
            flow_accum=fa,
            threshold=self.stream_threshold,
            output=self.file_path,
        )

        quest_metadata = {
            'parameter': 'streams',
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata)

        return {'datasets': new_dset}

class WBTWatershedDelineationWorkflow(ToolBase):
    _name = 'wbt-watershed-delineation-workflow'

    # metadata attributes
    group = 'raster'
    operates_on_datatype = ['raster']
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = ['raster']
    produces_geotype = None
    produces_parameters = None

    elevation_dataset = util.param.DatasetSelector(
        default=None,
        doc="""Dataset to run tool on.""",
        filters={'datatype': 'raster'},
    )

    streams_dataset = util.param.DatasetSelector(
        default=None,
        doc="""Dataset to run tool on.""",
        filters={'datatype': 'raster'},
    )

    outlet_features = util.param.FeatureSelector(
        default=None,
        doc="""Point feature to use for the outlet.""",
        filters={'geom_type': 'point'},
    )

    snap_distance = param.Number(
        default=0,
        bounds=(0,1000),  # TODO is there a way to not have an upper bound?
        doc="""snap distance in map units. If 0 no snapping will be performed.""",
    )

    SNAP_DISTANCE_ALGORITHMS = {
        'nearest-stream': wbt.jenson_snap_pour_points,
        'highest-accumulation': wbt.snap_pour_points,
    }
    algorithm = param.ObjectSelector(
        default='nearest-stream',
        doc="""algorithm to use for filling the dem""",
        objects=list(SNAP_DISTANCE_ALGORITHMS.keys()),
    )

    def _run_tool(self):
        dataset = self.elevation_dataset

        # get metadata, path etc from dataset

        orig_metadata = get_metadata(dataset)[dataset]
        collection_name = orig_metadata['collection']
        elev_file = orig_metadata['file_path']

        try:
            original_outlets = [f['geometry'] for f in get_metadata(self.outlet_features)]
        except:
            original_outlets = self.outlet_features

        new_dset = new_dataset(
            feature=orig_metadata['feature'],
            source='derived',
            # display_name=self.display_name,
            description=self.description
        )

        self.set_display_name(new_dset)

        prj = os.path.dirname(active_db())
        dst = os.path.join(prj, collection_name, new_dset)
        util.mkdir_if_doesnt_exist(dst)
        self.file_path = os.path.join(dst, new_dset + '.tiff')

        d8 = wbt.d8_pointer(elev_file)
        point_shp = points_to_shp(original_outlets)

        if self.snap_distance > 0:
            pp = wbt.vector_points_to_raster(point_shp, base=elev_file)
            snap_options = {
                'pour_pts': pp,
                'snap_dist': self.snap_distance,
            }
            fa = None
            if self.algorithm == 'nearest-stream':
                st = self.streams_dataset
                if st:
                    st = open_dataset(st)
                else:
                    fa = wbt.d_inf_flow_accumulation(elev_file)
                    st = wbt.extract_streams(fa, threshold=.1)
                snap_options.update(streams=st)
            else:
                fa = fa or wbt.d_inf_flow_accumulation(elev_file)
                # fa = wbt.d8_flow_accumulation(elev_file)
                snap_options.update(flow_accum=fa)

            snap_function = self.SNAP_DISTANCE_ALGORITHMS[self.algorithm]
            snapped = snap_function(**snap_options)

            indices = np.nonzero(np.nan_to_num(snapped))
            snapped_outlets = [(snapped.x.values[row], snapped.y.values[col]) for col, row in zip(*indices)]
            point_shp = points_to_shp(snapped_outlets)

        wbt.watershed(
            d8_pntr=d8,
            pour_pts=point_shp,
            output=self.file_path,
        )

        new_features = raster_to_polygons(self.file_path)

        quest_metadata = {
            'parameter': 'streams',
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'file_path': self.file_path,
        }

        update_metadata(new_dset, quest_metadata=quest_metadata)

        return {'datasets': new_dset, 'features': [new_features, snapped_outlets]}