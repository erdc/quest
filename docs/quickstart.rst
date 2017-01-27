Quickstart
==========

>>> import quest
>>> services = quest.api.get_services() #as python dict
>>> services_json = quest.api.get_services(as_json=True) #as pretty printed json string