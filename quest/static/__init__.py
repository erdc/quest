class DatasetStatus:
    """
    Enum of string constants representing dataset statuses.
    """
    NOT_STAGED = 'not staged'
    STAGED = 'staged for download'
    FAILED_DOWNLOAD = 'failed download'
    DOWNLOADED = 'downloaded'
    PENDING = 'pending'
    FILTERED = 'filter applied'


class ServiceType:
    GEO_DISCRETE = 'geo-discrete'
    GEO_SEAMLESS = 'geo-seamless'
    NON_GEO = 'non-geo'


class GeomType:
    POINT = 'Point'
    LINE = 'Line'
    POLYGON = 'Polygon'


class DataType:
    TIMESERIES = 'timeseries'
    RASTER = 'raster'


class FilterGroup:
    pass
