from rest_framework.pagination import PageNumberPagination
from rental_guru.utils import CustomResponse
from rental_guru.constants import Success


class KYCRequestsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        response_data = {'data': {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        },
        'message': Success.KYC_LIST}
        return CustomResponse(response_data)


class PropertiesPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 100
    message = Success.PROPERTIES_LIST

    def get_paginated_response(self, data):
        response_data = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return CustomResponse({'data': response_data, 'message': self.message})


class UnitsPagination(PropertiesPagination):
    page_size = 8
    message = Success.UNITS_LIST


class DocumentsPagination(PropertiesPagination):
    page_size = 10
    message = Success.DOCUMENTS_LIST


class VendorInvitationPagination(PropertiesPagination):
    page_size = 10
    message = Success.VENDOR_INVITATIONS_LIST


class TenantInvitationPagination(PropertiesPagination):
    page_size = 10
    message = Success.TENANT_INVITATIONS_LIST


class UserPropertiesAndUnitsPagination(PropertiesPagination):
    page_size = 10
    message = Success.USER_PROPERTIES_AND_UNITS_LIST
