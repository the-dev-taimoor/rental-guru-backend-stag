from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import Property, Unit
from apps.property_management.interface.serializers import (
    PropertyRetrieveSerializer,
    PropertySerializer,
    PropertySummaryRetrieveSerializer,
    UnitRetrieveSerializer,
)
from common.utils import CustomResponse

from .general import GeneralViewSet


class PropertyRetrieveViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        property_instance = self.get_object()
        all_data = self.get_combined_data(property_instance, property_instance.id, unit_instance=None, unit_id=None)
        all_data['units'] = list()
        unit_instances = Unit.objects.filter(property=property_instance.id)
        for unit_instance in unit_instances:
            unit_data = self.get_combined_data(property_instance, property_instance.id, unit_instance, unit_instance.id)
            all_data['units'].append(unit_data)
        return CustomResponse({'data': all_data})

    def get_combined_data(self, property_instance, property_id, unit_instance, unit_id):
        details_serializer = PropertyRetrieveSerializer(property_instance)
        unit_data = {
            'rental_details': PropertySummaryRetrieveSerializer.get_rental_details(property_id, unit_id),
            'amenities': PropertySummaryRetrieveSerializer.get_amenities(property_id, unit_id=unit_id),
            'cost_fees': PropertySummaryRetrieveSerializer.get_cost_fees(property_id, unit_id),
            'documents': PropertySummaryRetrieveSerializer.get_documents(property_id, unit_id),
        }
        if not unit_id:
            property_data = {
                'detail': details_serializer.data,
                'listing_info': PropertySummaryRetrieveSerializer.get_listing_info(property_id),
                'owners': PropertySummaryRetrieveSerializer.get_owners(property_id),
            }
            unit_data.update(property_data)
        else:
            unit_details_serializer = UnitRetrieveSerializer(unit_instance)
            property_data = {'detail': unit_details_serializer.data}
            unit_data.update(property_data)

        return unit_data
