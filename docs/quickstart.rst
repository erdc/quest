Quickstart
==========

>>> import dsl
>>> services = dsl.api.get_services() #as python dict
>>> services_json = dsl.api.get_services(as_json=True) #as pretty printed json string