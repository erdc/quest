"""
    api definition
"""

def get_sources(config=None):
    """Fetches list of data sources available in the data services library
    """
    pass


def add_source(source_name, source_type, metadata):
    """Add source to data services library
    """
    pass


def edit_source(source_name, source_type, metadata):
    """modify a source in the data services library
    """
    pass


def delete_source(source_name):
    """Delete a source from data services library
    """
    pass


def get_locations(source, parameter=None, bounding_poly=None, 
                  start_time=None, end_time=None, period=None):
    """Fetches location data for a given source (points, lines, polygons)
    """
    pass


def get_data(source, identifiers, **kwargs):
    """Fetches data for a list of identifiers. Not sure what the kwargs 
    should be yet
    """
    pass


def get_available_filters(source_type):
    """Fetches list of available filters for the source source_type
    """
    pass


def get_filter(filter_name):
    """Fetches requires params for filter, may be able to combine this 
    with get_available_filters, by returning a dictionary
    """
    pass


def apply_filter(dataset, filter):
    """Apply filter to dataset
    """
    pass


