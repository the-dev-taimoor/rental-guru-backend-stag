from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import ListingInfo, Property, PropertyPhoto
from apps.property_management.interface.serializers import ListingInfoSerializer, ListingInfoUpdateSerializer
from common.constants import Error, Success
from common.utils import CustomResponse

from .general import GeneralViewSet


class ListingInfoViewSet(GeneralViewSet):
    queryset = ListingInfo.objects.all()
    serializer_class = ListingInfoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_listing_object(self):
        try:
            property_instance = Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)
        try:
            return ListingInfo.objects.get(property_id=property_instance.id)
        except ListingInfo.DoesNotExist:
            raise NotFound(Error.LISTING_INFO_NOT_FOUND)

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_listing_object()
        serializer = ListingInfoUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        existing_photos = serializer.validated_data.pop('existing_photos', [])
        # delete every photo _not_ in the keep-list
        PropertyPhoto.objects.filter(property=serializer.instance.property).exclude(id__in=existing_photos).delete()
        # add new photos
        photos = request.FILES.getlist('photo') if request else []
        for photo in photos:
            PropertyPhoto.objects.create(property=serializer.instance.property, photo=photo)
        self.perform_update(serializer)
        return CustomResponse({'data': serializer.data, 'message': Success.LISTING_INFO_UPDATED})
