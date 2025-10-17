from rest_framework.permissions import IsAuthenticated

from apps.properties.infrastructure.models import Unit
from apps.properties.interface.serializers import PropertySummaryRetrieveSerializer, UnitRetrieveSerializer, UnitSerializer
from common.utils import CustomResponse

from .general import GeneralViewSet


class UnitSummaryViewSet(GeneralViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        unit_instance = self.get_object()
        property_instance = unit_instance.property
        all_data = self.get_combined_data(property_instance, property_instance.id, unit_instance, unit_instance.id)
        return CustomResponse({'data': all_data})

    def get_combined_data(self, property_instance, property_id, unit_instance, unit_id):
        details_serializer = UnitRetrieveSerializer(unit_instance)
        unit_data = {
            'detail': details_serializer.data,
            'rental_details': PropertySummaryRetrieveSerializer.get_rental_details(property_id, unit_id),
            'amenities': PropertySummaryRetrieveSerializer.get_amenities(property_id, unit_id=unit_id),
            'cost_fees': PropertySummaryRetrieveSerializer.get_cost_fees(property_id, unit_id),
            'documents': PropertySummaryRetrieveSerializer.get_documents(property_id, unit_id),
        }
        return unit_data
