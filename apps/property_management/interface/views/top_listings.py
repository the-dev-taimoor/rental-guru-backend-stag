from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import Property
from apps.property_management.interface.serializers import PropertySerializer

from .general import GeneralViewSet


class TopListingsViewSet(GeneralViewSet):
    queryset = Property.objects.filter(published=True)
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.order_by('-created_at')[:8]
