import django_filters
from django.db.models import Q

from apps.property_management.infrastructure.models import Unit


class DocumentFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_q', label='Keyword search')

    class Meta:
        model = Unit
        fields = ['q']

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(document_type__icontains=value) | Q(visibility__icontains=value) | Q(created_at__icontains=value)
        )
