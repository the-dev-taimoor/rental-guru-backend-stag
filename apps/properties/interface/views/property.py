from .general import GeneralViewSet

from apps.properties.infrastructure.models import Property
from apps.properties.interface.serializers import PropertySerializer
from apps.properties.application.pagination import PropertiesPagination
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.properties.infrastructure.filters import PropertyFilter
from rest_framework.decorators import action

from common.utils import CustomResponse
from common.constants import Success, Error
from rest_framework import status
from datetime import datetime
from rest_framework.exceptions import NotFound
from apps.user_authentication.application.permissions import IsKYCApproved, IsPropertyOwner

class PropertyViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    pagination_class = PropertiesPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PropertyFilter
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'], url_path='publish', permission_classes=[IsAuthenticated, IsKYCApproved, IsPropertyOwner])
    def publish(self, request, pk=None):
        try:
            property = self.get_object()
        except Property.DoesNotExist:
            return CustomResponse({"error": Error.PROPERTY_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        published = request.data.get('published', None)
        if published is None:
            return CustomResponse({"error": Error.PUBLISHED_FIELD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        property.published = published
        property.published_at = datetime.now() if published else None
        property.save()

        serializer = self.get_serializer(property)

        return CustomResponse({"message": Success.PROPERTY_PUBLISHED_STATUS, "data": serializer.data},
                        status=status.HTTP_200_OK)

    def get_queryset(self):
        return self.queryset.filter(property_owner=self.request.user)

    def get_object(self):
        try:
            return Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)