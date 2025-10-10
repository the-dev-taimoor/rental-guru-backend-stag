
from rest_framework import status, permissions
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from common.constants import Success
from common.utils import CustomResponse

from apps.user_authentication.infrastructure.models import ServiceSubCategory


class ServiceSubCategoriesView(ModelViewSet):
    """
    To get the list of pre-saved sub-categories for vendor offered services.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceSubCategory.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category_id']

    def list(self, request, *args, **kwargs):
        subcategories = self.filter_queryset(self.queryset.values('id', 'name'))
        result = list(subcategories)

        return CustomResponse({'data': result, 'message': Success.SERVICE_SUBCATEGORIES}, status=status.HTTP_200_OK)
