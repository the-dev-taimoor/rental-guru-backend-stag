from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import Amenities, Property, PropertyAssignedAmenities, PropertyTypeAndAmenity, Unit
from apps.property_management.interface.serializers import PropertyAmenitiesSerializer, PropertySummaryRetrieveSerializer
from common.constants import Success
from common.utils import CustomResponse

from .general import GeneralViewSet


class AmenitiesView(GeneralViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PropertyTypeAndAmenity.objects.all()
    serializer_class = PropertyAmenitiesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property_type']

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        page_saved = serializer.validated_data.get('page_saved')
        property_id = serializer.validated_data['property_id']
        sub_amenities_ids = serializer.validated_data.get('sub_amenities', [])
        other_amenities = serializer.validated_data.get('other_amenities', [])
        unit_id = serializer.validated_data.get('unit_id', None)

        property_obj = get_object_or_404(Property, id=property_id)

        if unit_id:
            unit_obj = get_object_or_404(Unit, id=unit_id)
        else:
            unit_obj = None

        PropertyAssignedAmenities.objects.filter(property=property_obj, unit=unit_obj).delete()

        bulk_list = []
        for sub_id in sub_amenities_ids:
            sub_obj = get_object_or_404(Amenities, id=sub_id)

            pa = PropertyAssignedAmenities(property=property_obj, sub_amenity=sub_obj, unit=unit_obj)
            bulk_list.append(pa)

        PropertyAssignedAmenities.objects.bulk_create(bulk_list)

        unit_id = None
        if unit_obj:
            obj = unit_obj
            unit_id = unit_obj.id
        else:
            obj = property_obj

        obj.other_amenities = other_amenities
        obj.page_saved = page_saved
        obj.save(update_fields=['other_amenities', 'page_saved'])

        amenities_data = PropertySummaryRetrieveSerializer.get_amenities(property_id=property_obj.id, unit_id=unit_id)

        return CustomResponse({'data': amenities_data, 'message': Success.AMENITIES_UPDATED}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        filtered_queryset = self.filter_queryset(self.get_queryset())
        amenity_ids = filtered_queryset.values_list('sub_amenities', flat=True)
        amenities = Amenities.objects.filter(id__in=amenity_ids)
        amenities_dict = {}
        for item in amenities:
            if item.amenity not in amenities_dict:
                amenities_dict[item.amenity] = []

            amenities_dict[item.amenity].append({'id': item.id, 'sub_amenity': item.sub_amenity})

        result = [{'amenity': key, 'sub_amenities': value} for key, value in amenities_dict.items()]

        return CustomResponse({'data': result, 'message': Success.AMENITIES_AND_SUB_AMENITIES}, status=status.HTTP_200_OK)
