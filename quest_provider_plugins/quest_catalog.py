from quest.plugins import ProviderBase, SingleFileServiceBase
from quest.database.database import select_catalog_entries
from quest.static import ServiceType
import pandas as pd

class QuestCatalogService(SingleFileServiceBase):
    service_name = 'quest'
    display_name = 'Quest Catalog Service'
    description = 'Quest Catalog uses a database for derived datasets from Quest.'
    service_type = ServiceType.GEO_DISCRETE
    unmapped_parameters_available = True
    geom_type = ['Point', 'Line', 'Polygon']
    datatype = None
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {}

    def search_catalog(self, **kwargs):

        return pd.DataFrame(select_catalog_entries())


class QuestCatalogProvider(ProviderBase):
    service_list = [QuestCatalogService]
    publisher_list = None
    display_name = 'Quest Catalog Provider'
    description = 'Services avaliable through the Quest catalog database.'
    organization_name = 'Quest'
    name = 'quest'
