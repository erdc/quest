from builtins import object
import abc
from future.utils import with_metaclass
from dsl import util


class WebServiceBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data services plugins
    """

    def __init__(self, use_cache=True, update_frequency='M'):
        self.use_cache = use_cache
        self.update_frequency = update_frequency
        self._register()

    def get_features(self, service, parameters=None, features=None, bbox=None, as_dataframe=False):
        """Get Features associated with service.

        Take a series of query parameters and return a list of 
        locations as a geojson python dictionary
        """        
        use_cache=False  
        as_dataframe=True 
        if use_cache:
            selected_features = _load_cache(self.name, service, update_frequency=update_frequency)
        else:
            selected_features = self._get_features(service)

        #apply filters
        if features:
            selected_features = selected_features.ix[features]

        if bbox:
            selected_features = util.filter_bbox(selected_features)

        if not as_dataframe:
            selected_features = util.df_to_geojson(selected_features)

        return selected_features

    def get_services(self, filters={}):
        return self._get_services()

    def get_parameters(self, service, features=None):
        return self._get_parameters(service)

    def get_parameter_list(self, service):
        pass

    @abc.abstractmethod
    def _register(self):
        """
        """

    @abc.abstractmethod
    def _get_services(self):
        """
        """

    @abc.abstractmethod
    def _get_features(self, service):
        """
        """

    @abc.abstractmethod
    def _get_parameters(self, services):
        """
        """

    @abc.abstractmethod
    def _download_data(self, feature, **kwargs):
        """
        """
