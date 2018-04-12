"""Plugin to create service from data in local/network folder

"""

from .. import util
from .base import ProviderBase, ServiceBase

import geojson
from geojson import Feature, FeatureCollection, Polygon
from io import StringIO
import pandas as pd
import os
import requests
import shutil
import yaml
import param


def get_user_service_base():

    class UserServiceBase(ServiceBase):
        parameter = param.ObjectSelector(default=None, doc="""parameter""")

        @classmethod
        def instance(cls, service_name, service_data, provider, uri, is_remote):
            parameters = util.listify(service_data['metadata'].pop('parameters'))

            if len(parameters) > 1:
                cls.params()['parameter'].objects = sorted(parameters)
            else:
                cls.params()['parameter'] = param.String(default=parameters[0], doc="""parameter""", constant=True)

            self = UserServiceBase(name=service_name, provider=provider)
            self.service_name = service_name
            self.uri = uri
            self.is_remote = is_remote

            self._parameter_map = {p: p for p in parameters}
            for k, v in service_data['metadata'].items():
                setattr(self, k, v)
            self.service_folder = util.listify(service_data['service_folder'])
            if len(self.service_folder) > 1:
                raise ValueError()  # Now only supporting one service folder
            else:
                self.service_folder = self.service_folder[0]
            self.features_file = service_data['features']['file']
            self.features_format = service_data['features']['format']
            self.datasets_mapping = service_data['datasets']['mapping']
            self.datasets_save_folder = service_data['datasets']['save_folder']
            self.datasets_metadata = service_data['datasets'].get('metadata', None)

            return self

        def download(self, feature, file_path, dataset, **kwargs):
            if self.datasets_mapping is not None:
                fnames = self.datasets_mapping
                if isinstance(dict, self.datasets_mapping):
                    fnames = self.dataset_mapping[self.parameter]
                fnames = [f.replace('<feature>', feature) for f in util.listify(fnames)]
            else:
                fnames = self.features.loc[feature]['_download_url']

            final_path = []
            for src, file_name in zip(self._get_paths(fnames), fnames):
                dst = file_path
                if self.dataset_save_folder is not None:
                    dst = os.path.join(dst, self.dataset_save_folder, self.svc_folder)

                dst = os.path.join(dst, file_name)
                base, _ = os.path.split(dst)
                util.mkdir_if_doesnt_exist(base)
                final_path.append(dst)
                if self.is_remote:
                    r = requests.get(src, verify=False)
                    if r.status_code == 200:  # only download if file exists
                        chunk_size = 64 * 1024
                        with open(dst, 'wb') as f:
                            for content in r.iter_content(chunk_size):
                                f.write(content)
                else:
                    if os.path.exists(src):
                        shutil.copyfile(src, dst)  # only copy if file exists

            # TODO need to deal with parameters if multiple params exist
            if len(final_path) == 1:
                final_path = final_path[0]
            else:
                final_path = ','.join(final_path)

            metadata = {
                'file_path': final_path,
                'file_format': self.file_format,
                'datatype': self.datatype,
                'parameter': self.parameters['parameters'][0],
            }

            if self.datasets_metadata is not None:
                metadata.update(self.datasets_metadata)
            return metadata

        def get_features(self, **kwargs):
            fmt = self.features_format
            paths = self._get_paths(self.features_file)

            all_features = []
            for p in util.listify(paths):
                with uri_open(p, self.is_remote) as f:
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

        def _get_paths(self, filenames):
            folder = self.service_folder
            paths = list()
            for filename in util.listify(filenames):
                if self.uri.startswith('http'):
                    paths.append(self.uri.rstrip('/') + '/{}/{}'.format(folder, filename))
                else:
                    paths.append(os.path.join(self.uri, folder, filename))
            return paths

    return UserServiceBase


class UserProvider(ProviderBase):
    service_base_class = None
    display_name = None
    description = None
    organization_name = None
    organization_abbr = None

    def __init__(self, uri, name=None, use_cache=True, update_frequency='M'):
        super(UserProvider, self).__init__(name=name, use_cache=use_cache, update_frequency=update_frequency)
        self.uri = uri
        self.is_remote = util.is_remote_uri(uri)
        self._register()

    @property
    def metadata(self):
        return self._metadata

    @property
    def services(self):
        return self._services

    def _register(self):
        """Register user service."""

        config_file = self._get_path('quest.yml')
        with uri_open(config_file, self.is_remote) as yml:
            provider_data = yaml.load(yml)
        self.name = provider_data['name']
        self._metadata = provider_data['metadata']
        self._metadata['service_uri'] = self.uri
        self._services = {name: get_user_service_base().instance(service_name=name,
                                                                 service_data=data,
                                                                 provider=self,
                                                                 uri=self.uri,
                                                                 is_remote=self.is_remote)
                          for name, data in provider_data['services'].items()}

    def _get_path(self, filename):
        uri = self.uri
        if uri.startswith('http'):
            path = uri.rstrip('/') + '/' + filename
        else:
            path = os.path.join(uri, filename)
        if isinstance(path, list) and len(path) == 1:
            path = path[0]
        return path


def uri_open(uri, is_remote):
    if is_remote:
        return StringIO(requests.get(uri, verify=False).text)
    else:
        return open(uri)
