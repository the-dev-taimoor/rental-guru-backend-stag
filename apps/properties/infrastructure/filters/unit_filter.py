import django_filters
from django.db.models import Q

from apps.properties.infrastructure.models import Unit


class UnitFilter(django_filters.FilterSet):
    published = django_filters.BooleanFilter(field_name='published')
    q = django_filters.CharFilter(method='filter_q', label='Keyword search')

    class Meta:
        model = Unit
        fields = ['published', 'q']

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            Q(number__icontains=value)
            | Q(type__icontains=value)
            | Q(floor_number__icontains=value)
            | Q(status__icontains=value)
            | Q(unit_rent_details__assigned_tenant__icontains=value)
        )
