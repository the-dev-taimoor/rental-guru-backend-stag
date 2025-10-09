from .general import GeneralViewSet

from apps.properties.infrastructure.models import Property
from apps.properties.interface.serializers import PropertySerializer
from rest_framework.permissions import IsAuthenticated


class TopListingsViewSet(GeneralViewSet):
    queryset = Property.objects.filter(published=True)
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.order_by('-created_at')[:8]