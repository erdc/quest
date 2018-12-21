Getting Options for Plugin Functions
====================================

Quest has thee types of plugins that enable easy expansion of capabilities:

    1. Provider plugins - these add new data services allowing data to be searched and downloaded from new sources.
    2. Filter plugins - these provide new operations that can be done on datasets to manipulate or transform them.
    3. I/O plugins - these allow Quest to read, write, open, and visualize new data formats.

Since the inputs required to the functions provided by each of these plugins can be different there are API calls that allow users to get the options that are required for a particular call. Options can be requested in various formats. The schema for the JSON options is the same regardless of the type of plugin.

The JSON format will always have two attributes:

    - `title` - a title for the options that can be used as the tile for a options dialog in a GUI.
    - `properties` - an ordered list of properties each representing an input to the function that can be represented by a GUI widget.

Each property will have the following attributes:

    - `name` - an identifier for the property.
    - `type` - the class name of the param Class that the property is an instance of.
    - `description` - details about the property.
    - `default` - the default value the property will have.

Depending on the `type` the following attributes may also be present:

    - `bound` - the upper and lower limits of valid values.
    - `range` - a list of name, value pairs that are valid options for the property.


Below is an example of a JSON description of the options for ncdc-ghcn service::

    {'properties': [{'default': None,
        'description': 'parameter',
        'name': 'parameter',
        'range': [['air_temperature:daily:mean', 'air_temperature:daily:mean'],
         ['air_temperature:daily:minimum', 'air_temperature:daily:minimum'],
         ['air_temperature:daily:total', 'air_temperature:daily:total'],
         ['rainfall:daily:total', 'rainfall:daily:total'],
         ['snow_depth:daily:total', 'snow_depth:daily:total'],
         ['snowfall:daily:total', 'snowfall:daily:total']],
        'type': 'ObjectSelector'},
       {'bounds': None,
        'default': None,
        'description': 'start date',
        'name': 'start',
        'type': 'Date'},
       {'bounds': None,
        'default': None,
        'description': 'end date',
        'name': 'end',
        'type': 'Date'}],
      'title': 'NCDC GHCN Daily Download Options'}

