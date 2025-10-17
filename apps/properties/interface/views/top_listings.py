from rest_framework.permissions import IsAuthenticated

from apps.properties.infrastructure.models import Property
from apps.properties.interface.serializers import PropertySerializer

from .general import GeneralViewSet


class TopListingsViewSet(GeneralViewSet):
    queryset = Property.objects.filter(published=True)
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.order_by('-created_at')[:8]
