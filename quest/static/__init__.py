class DatasetStatus:
    """
    Enum of string constants representing dataset statuses.
    """
    NOT_STAGED = 'not staged'
    STAGED = 'staged for download'
    FAILED_DOWNLOAD = 'failed download'
    DOWNLOADED = 'downloaded'
    PENDING = 'pending'
    DERIVED = 'tool applied'


class ServiceType:
    GEO_DISCRETE = 'geo-discrete'
    GEO_SEAMLESS = 'geo-seamless'
    NON_GEO = 'non-geo'


class GeomType:
    POINT = 'Point'
    LINE = 'Line'
    POLYGON = 'Polygon'


class UriType:
    COLLECTION = 'collections'
    DATASET = 'datasets'
    SERVICE = 'services'
    PUBLISHER = 'publishers'


class DataType:
    TIMESERIES = 'timeseries'
    RASTER = 'raster'


class FilterGroup:
    pass


class DatasetSource:
    DERIVED = 'derived'
    WEB_SERVICE = 'download'
    USER = 'user-created'


class PluginType:
    IO = 'io'
    TOOL = 'tool'
    PROVIDER = 'provider'
