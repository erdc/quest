import abc

from ...database import get_db, db_session


class ProviderBase(metaclass=abc.ABCMeta):
    """Base class for data provider plugins
    """
    name = None
    service_list = None
    publisher_list = None
    display_name = None
    description = None
    organization_name = None
    organization_abbr = None
    use_cache = True

    @property
    def services(self):
        if self.service_list is None:
            return {}
        if self._services is None:
            self._services = {s.service_name: s(name=s.service_name, provider=self) for s in self.service_list}

        return self._services

    @property
    def publishers(self):
        if self.publisher_list is None:
            return {}
        if self._publishers is None:
            self._publishers = {p.publisher_name: p(name=p.publisher_name, provider=self) for p in self.publisher_list}

        return self._publishers

    @property
    def metadata(self):
        return {
            'display_name': self.display_name,
            'description': self.description,
            'organization': {
                'abbr': self.organization_abbr,
                'name': self.organization_name,
            }
        }

    @property
    def credentials(self):
        if self._credentials is None:
            db = get_db()
            with db_session:
                p = db.Providers.select().filter(provider=self.name).first()
                if p is None:
                    raise ValueError('The {0} Provider has not been authenticated yet. Please call quest.api.authenticate_provider({0})'.format(self.name))
                else:
                    self._credentials = dict(username=p.username, password=p.password)

        return self._credentials

    def __init__(self, name=None, use_cache=None, update_frequency='M'):
        self.name = name or self.name
        self.use_cache = use_cache or self.use_cache
        self.update_frequency = update_frequency  # not implemented
        self._services = None
        self._publishers = None
        self._credentials = None

    def search_catalog(self, service, update_cache=False, **kwargs):
        """Get catalog_entries associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        return self.services[service].search_catalog_wrapper(update_cache=update_cache, **kwargs)

    def get_tags(self, service, update_cache=False):
        return self.services[service].get_tags(update_cache=update_cache)

    def get_services(self):
        return {k: v.metadata for k, v in self.services.items()}

    def get_publishers(self):
        return {k: v.metadata for k, v in self.publishers.items()}

    def get_parameters(self, service, catalog_ids=None):
        return self.services[service].get_parameters(catalog_ids=catalog_ids)

    def download(self, service, catalog_id, file_path, dataset, **kwargs):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].download(catalog_id, file_path, dataset, **kwargs)

    def get_download_options(self, service, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].get_download_options(fmt)

    def publish(self, publisher, **kwargs):
        return self.publishers[publisher].publish(**kwargs)

    def publish_options(self, publisher, fmt):
        return self.publishers[publisher].publish_options(fmt)

    def authenticate_me(self, **kwargs):
        raise NotImplementedError

    def unauthenticate_me(self):
        db = get_db()
        with db_session:
            p = db.Providers.select().filter(provider=self.name).first()
            if p is None:
                raise ValueError('Provider does not exist in the database.')
            else:
                p.delete()
