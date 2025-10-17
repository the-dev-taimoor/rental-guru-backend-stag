import django_filters
from django.db.models import Count, Q

from apps.properties.infrastructure.models import Property


class PropertyFilter(django_filters.FilterSet):
    published = django_filters.BooleanFilter(field_name='published')
    city = django_filters.CharFilter(field_name='city', lookup_expr='exact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    property_type = django_filters.CharFilter(field_name='property_type', lookup_expr='exact')
    rental_type = django_filters.CharFilter(field_name='property_rent_details__rental_type', lookup_expr='exact')
    availability_date = django_filters.CharFilter(field_name='property_slots__date', lookup_expr='exact', method='filter_availability_date')
    number_of_units = django_filters.CharFilter(field_name='property_photos__unit', lookup_expr='exact', method='filter_availability_date')
    unit_count = django_filters.RangeFilter(method='filter_unit_count', label='Unit count range')
    q = django_filters.CharFilter(method='filter_q', label='Keyword search')

    class Meta:
        model = Property
        fields = ['property_type', 'published', 'city', 'rental_type', 'unit_count', 'q']

    def filter_availability_date(self, queryset, name, value):
        """Because unavailable dates stored in table, so while filtering for an available date exclude those
        properties which are having that date as unavailable in table."""
        if value:
            return queryset.exclude(property_slots__date=value)
        return queryset

    def filter_unit_count(self, queryset, name, value):
        """
        Annotate each Property with unit_count = Count(unit_property)
        then apply the range bounds if provided.
        `value` will be a tuple (min, max) or a Range object with .start/.stop
        """
        qs = queryset.annotate(unit_count=Count('unit_property'))
        try:
            lower, upper = value.start, value.stop
        except AttributeError:
            lower, upper = value[0], value[1]

        if lower is not None:
            qs = qs.filter(unit_count__gte=lower)
        if upper is not None:
            qs = qs.filter(unit_count__lte=upper)

        return qs

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(street_address__icontains=value) | Q(city__icontains=value) | Q(state__icontains=value)
        )
