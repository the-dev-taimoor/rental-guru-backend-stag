from common.pagination.base import BasePagination
from common.constants import Success

class PropertiesPagination(BasePagination):
    page_size = 8
    message = Success.PROPERTIES_LIST

class UnitsPagination(BasePagination):
    page_size = 8
    message = Success.UNITS_LIST

class DocumentsPagination(BasePagination):
    message = Success.DOCUMENTS_LIST

class UserPropertiesAndUnitsPagination(BasePagination):
    message = Success.USER_PROPERTIES_AND_UNITS_LIST
