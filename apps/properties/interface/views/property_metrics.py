from .general import GeneralViewSet

from apps.properties.infrastructure.models import Property
from apps.properties.interface.serializers import PropertySerializer
from rest_framework.permissions import IsAuthenticated
from common.utils import CustomResponse
from common.constants import Success

# this has dummy response
class PropertyMetricsViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # property_instance = self.get_object()
        all_data = dict()
        all_data['rental_income'] = '-'
        all_data['occupancy_rate'] = '-'
        all_data['avg_lease_term'] = '-'
        all_data['avg_tenant_rating'] = '-'
        return CustomResponse({'data': all_data, 'message': Success.PROPERTY_METRICS})