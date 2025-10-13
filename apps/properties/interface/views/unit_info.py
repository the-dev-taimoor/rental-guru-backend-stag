from .general import GeneralViewSet

from apps.properties.infrastructure.models import Property,Unit, PropertyPhoto
from apps.properties.interface.serializers import UnitSerializer, UnitUpdateSerializer
from apps.properties.application.pagination import UnitsPagination
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.properties.filters import UnitFilter
from rest_framework.decorators import action

from common.utils import CustomResponse
from common.constants import Success, Error
from rest_framework import status
from datetime import datetime
from apps.user_authentication.application.permissions import IsKYCApproved, IsUnitOwner
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

class UnitInfoViewSet(GeneralViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    pagination_class = UnitsPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UnitFilter
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = UnitUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        existing_photos = serializer.validated_data.pop('existing_photos', [])
        # delete every photo _not_ in the keep-list
        PropertyPhoto.objects.filter(unit=serializer.instance).exclude(id__in=existing_photos).delete()
        # add new photos
        photos = request.FILES.getlist('photo') if request else []
        for photo in photos:
            PropertyPhoto.objects.create(property=serializer.instance.property, unit=serializer.instance, photo=photo)
        self.perform_update(serializer)
        return CustomResponse({
            'message': Success.UNIT_INFO_UPDATED,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='publish', permission_classes=[IsAuthenticated, IsKYCApproved, IsUnitOwner])
    def publish(self, request, pk=None):
        try:
            unit = self.get_object()
        except Property.DoesNotExist:
            return CustomResponse({"error": Error.UNIT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        published = request.data.get('published', None)

        if published is None:
            return CustomResponse({"error": Error.PUBLISHED_FIELD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        unit.published = published
        unit.published_at = datetime.now() if published else None
        unit.save()

        serializer = self.get_serializer(unit)

        return CustomResponse({"message": Success.UNIT_PUBLISHED_STATUS, "data": serializer.data},
                              status=status.HTTP_200_OK)

    def get_queryset(self):
        property_id = self.request.query_params.get('property')
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)
        return self.queryset.filter(property=property_id)

    def get_object(self):
        try:
            unit = Unit.objects.get(id=self.kwargs['pk'])
            # Ensure user owns the property
            if hasattr(self.request, 'user') and unit.property.property_owner != self.request.user:
                raise PermissionDenied(Error.UNIT_NOT_OWNED)
            return unit
        except Unit.DoesNotExist:
            raise NotFound(Error.UNIT_NOT_FOUND)