"""Plugin to create service from data in local/network folder

"""

from .. import util
from .base import WebServiceBase

import geojson
from geojson import Feature, FeatureCollection, Polygon
from io import StringIO
import pandas as pd
import os
import requests
import shutil
import yaml


class UserService(WebServiceBase):
    def __init__(self, uri, name=None, use_cache=True, update_frequency='M'):
        self.name = name
        self.uri = uri
        self.is_remote = util.is_remote_uri(uri)
        self.use_cache = use_cache  # not implemented
        self.update_frequency = update_frequency  # not implemented
        self._register(uri)

    def _register(self, uri):
        """Register user service."""

        config_file = self._get_path('quest.yml')
        c = yaml.load(self.uri_open(config_file))
        self.metadata = c['metadata']
        self.metadata['service_uri'] = uri
        self.services = c['services']
        self.name = c['name']

    def _get_services(self):
        return {k: v['metadata'] for k, v in self.services.items()}

    def _get_features(self, service):
        fmt = self.services[service]['features']['format']
        features_file = self.services[service]['features']['file']
        path = self._get_path(features_file, service)

        all_features = []
        for p in util.listify(path):
            with self.uri_open(p) as f:
                if fmt.lower() == 'geojson':
                    features = geojson.load(f)
                    features = util.to_geodataframe(features)

                if fmt.lower() == 'mbr':
                    # TODO creating FeatureCollection not needed anymore
                    # this can be rewritten as directly creating a pandas dataframe
                    polys = []
                    # skip first line which is a bunding polygon
                    f.readline()
                    for line in f:
                        feature_id, x1, y1, x2, y2 = line.split()
                        properties = {}  # '_service_id': feature_id}
                        polys.append(Feature(geometry=util.bbox2poly(x1, y1, x2, y2, as_geojson=True), properties=properties, id=feature_id))
                    features = FeatureCollection(polys)
                    features = util.to_geodataframe(features)

                if fmt.lower() == 'mbr-csv':
                    # TODO merge this with the above,
                    # mbr format from datalibrary not exactly the same as
                    # mbr fromat in quest-demo-data
                    polys = []
                    for line in f:
                        feature_id, y1, x1, y2, x2 = line.split(',')
                        feature_id = feature_id.split('.')[0]
                        properties = {}  # '_service_id': feature_id}
                        polys.append(Feature(geometry=util.bbox2poly(x1, y1, x2, y2, as_geojson=True), properties=properties, id=feature_id))
                    features = FeatureCollection(polys)
                    features = util.to_geodataframe(features)

                if fmt.lower() == 'isep-json':
                    # uses exported json file from ISEP DataBase
                    # assuming ISEP if a geotypical service for now.
                    features = pd.read_json(p)
                    features.rename(columns={'_id': 'service_id'}, inplace=True)
                    features['download_url'] = features['files'].apply(lambda x: os.path.join(x[0].get('file location'), x[0].get('file name')))
                    # remove leading slash from file path
                    features['download_url'] = features['download_url'].str.lstrip('/')
                    features['parameters'] = 'met'

            all_features.append(features)

        # drop duplicates fails when some columns have nested list/tuples like
        # _geom_coords. so drop based on _service_id
        features = pd.concat(all_features)
        features = features.drop_duplicates(subset='service_id')
        features.index = features['service_id']
        features.sort_index(inplace=True)
        return features

    def _get_parameters(self, service, features=None):
        metadata = self.services[service]['metadata']
        params = metadata['parameters']
        param_codes = metadata.get('parameter_codes', params)
        return {
            'parameters': params,
            'parameter_codes': param_codes,
        }

    def _download(self, service, feature, save_path, dataset, parameter=None, **kwargs):
        datasets = self.services[service]['datasets']
        save_folder = datasets.get('save_folder')
        mapping = datasets.get('mapping')
        if mapping is not None:
            fname = mapping.replace('<feature>', feature)
        else:
            fname = self._get_features(service).ix[feature]['_download_url']

        final_path = []
        if parameter is not None:
            fname = fname.replace('<parameter>', parameter)
        path = self._get_path(fname, service)
        service_folder = self.services[service].get('service_folder', [''])
        for src, svc_folder in zip(util.listify(path), util.listify(service_folder)):
            dst = save_path
            if save_folder is not None:
                dst = os.path.join(dst, save_folder, svc_folder)

            dst = os.path.join(dst, fname)
            base, _ = os.path.split(dst)
            util.mkdir_if_doesnt_exist(base)
            final_path.append(dst)
            if self.is_remote:
                r = requests.get(src, verify=False)
                if r.status_code==200: # only download if file exists
                    chunk_size = 64 * 1024
                    with open(dst, 'wb') as f:
                        for content in r.iter_content(chunk_size):
                            f.write(content)
            else:
                if os.path.exists(src):
                    shutil.copyfile(src, dst)  # only copy if file exists

        # TODO copy common files
        # May not be needed anymore
        # print('value =', kwargs.get('copy_common'))
        # print('src=', src_path)
        # if kwargs.get('copy_common'):
        #    common_files = [f for f in os.listdir(src_path) if os.path.isfile(os.path.join(src_path,f))]
        #     print('files=', common_files)
        #    for f in common_files:
        #        print('copying common file: ', f)
        #        shutil.copy(os.path.join(src_path,f), path)

        # TODO need to deal with parameters if multiple params exist
        if len(final_path) == 1:
            final_path = final_path[0]
        else:
            final_path = ','.join(final_path)

        metadata = {
            'save_path': final_path,
            'file_format': self.services[service]['metadata'].get('file_format'),
            'datatype': self.services[service]['metadata'].get('datatype'),
            'parameter': self.services[service]['metadata'].get('parameters')[0],
        }
        extra_meta = datasets.get('metadata')
        if extra_meta is not None:
            metadata.update(extra_meta)
        return metadata

    def _download_options(self, service, fmt='json-schema'):
        # TODO if more than one parameter available
        if fmt == 'smtk':
            schema = ''

        if fmt == 'json-schema':
            schema = {}

        return schema

    def _get_path(self, filename, service=None):
        uri = self.uri
        if service is None:
            if uri.startswith('http'):
                path = uri.rstrip('/') + '/' + filename
            else:
                path = os.path.join(uri, filename)
        else:
            folder = self.services[service].get('service_folder')
            if folder is None:
                return self._get_path(filename)
            else:
                if not isinstance(folder, list):
                    folder = [folder]
                path = []
                for f in folder:
                    if uri.startswith('http'):
                        path.append(uri.rstrip('/') + '/{}/{}'.format(f, filename))
                    else:
                        path.append(os.path.join(uri, f, filename))
        if isinstance(path, list) and len(path) == 1:
            path = path[0]
        return path

    def uri_open(self, uri):
        if self.is_remote:
            return StringIO(requests.get(uri, verify=False).text)
        else:
            return open(uri)
