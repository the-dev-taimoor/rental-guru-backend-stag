from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import Property, RentDetails
from apps.property_management.interface.serializers import RentDetailsSerializer
from common.constants import Error, Success
from common.utils import CustomResponse

from .general import GeneralViewSet


class RentalDetailViewSet(GeneralViewSet):
    queryset = RentDetails.objects.all()
    serializer_class = RentDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_rental_object(self):
        try:
            property_instance = Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)
        unit_id = self.kwargs.get('unit', None)
        try:
            return RentDetails.objects.get(property_id=property_instance.id, unit_id=unit_id)
        except RentDetails.DoesNotExist:
            raise NotFound(Error.RENTAL_DETAIL_NOT_FOUND.format('unit' if unit_id else 'property'))

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        request_data = request.data
        self.kwargs['unit'] = request_data.get('unit')
        partial = kwargs.pop('partial', False)
        instance = self.get_rental_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return CustomResponse({'data': serializer.data, 'message': Success.RENTAL_INFO_UPDATED})
