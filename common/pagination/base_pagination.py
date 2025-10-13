from rest_framework.pagination import PageNumberPagination
from common.utils import CustomResponse

class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    message = None

    def get_paginated_response(self, data):
        response_data = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return CustomResponse({'data': response_data, 'message': self.message})
