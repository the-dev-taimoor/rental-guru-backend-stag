from django.db.models import Prefetch
from rest_framework import permissions, status
from rest_framework.viewsets import ModelViewSet

from apps.user_authentication.infrastructure.models import ServiceCategory, ServiceSubCategory
from common.constants import Success
from common.dummy_serializer import DummySerializer
from common.utils import CustomResponse


class ServiceCategoriesView(ModelViewSet):
    """
    To get the list of pre-saved categories for vendor offered services.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceCategory.objects.all()

    def get_serializer_class(self):
        return DummySerializer

    def list(self, request, *args, **kwargs):
        subcategories_qs = ServiceSubCategory.objects.all()
        categories = self.queryset.prefetch_related(Prefetch('category', queryset=subcategories_qs, to_attr='subcategories_list'))

        categories_list = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'subcategories': [{'id': sub.id, 'name': sub.name} for sub in category.subcategories_list],
            }
            categories_list.append(category_data)

        return CustomResponse({'data': categories_list, 'message': Success.SERVICE_CATEGORIES}, status=status.HTTP_200_OK)
