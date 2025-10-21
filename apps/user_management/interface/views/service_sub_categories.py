from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.viewsets import ModelViewSet

from apps.user_management.infrastructure.models import ServiceSubCategory
from common.constants import Success
from common.dummy_serializer import DummySerializer
from common.utils import CustomResponse


class ServiceSubCategoriesView(ModelViewSet):
    """
    To get the list of pre-saved sub-categories for vendor offered services.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceSubCategory.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category_id']

    def get_serializer_class(self):
        return DummySerializer

    def list(self, request, *args, **kwargs):
        subcategories = self.filter_queryset(self.queryset.values('id', 'name'))
        result = list(subcategories)

        return CustomResponse({'data': result, 'message': Success.SERVICE_SUBCATEGORIES}, status=status.HTTP_200_OK)
