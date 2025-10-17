from datetime import datetime, timedelta

from apps.properties.infrastructure.models import CalendarSlot
from apps.properties.interface.serializers import CalendarSlotListSerializer, CalendarSlotSerializer
from common.constants import Error, Success
from common.utils import CustomResponse

from .general import GeneralViewSet


class CalendarSlotViewSet(GeneralViewSet):
    queryset = CalendarSlot.objects.all()
    serializer_class = CalendarSlotSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of all dates for a specific month and year.
        """
        serializer = CalendarSlotListSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        month = data.get('month')
        year = data.get('year')
        property = data.get('property')
        unit = data.get('unit')

        if not month or not year:
            return CustomResponse({"error": "Month and Year are required"}, status=400)

        # Generate the first and last day of the month
        start_date = datetime(year=int(year), month=int(month), day=1)
        end_date = datetime(year=int(year), month=int(month), day=28)  # To ensure we don't overflow on February
        # Adjust end_date to the last day of the month
        while True:
            try:
                end_date = end_date.replace(day=28) + timedelta(days=4)  # this will always get us to the next month
                end_date = end_date - timedelta(days=end_date.day)
                break
            except ValueError:
                pass

        slots = CalendarSlot.objects.filter(date__gte=start_date, date__lte=end_date, property=property, unit=unit)

        # Create a list of all dates of the month, defaulting to available
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            status = 'available'
            # Check if the date is in the database and has a status of 'unavailable'
            existing_slot = slots.filter(date=current_date).first()
            if existing_slot:
                status = existing_slot.status
            all_dates.append(
                {
                    'id': existing_slot.id if existing_slot else None,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'status': status,
                    'reason': existing_slot.reason if existing_slot else None,
                }
            )
            current_date += timedelta(days=1)

        return CustomResponse({"data": all_dates})

    def create(self, request, *args, **kwargs):
        """
        Create unavailable slots based on provided dates.
        """
        property = request.data.get('property')
        unit = request.data.get('unit')
        data_ = request.data.get('unavailable_dates')

        if not data_:
            return CustomResponse({"error": Error.UNAVAILABLE_DATES_REQUIRED}, status=400)

        for data in data_:
            data['status'] = 'unavailable'
            data['property'] = property
            data['unit'] = unit
            serializer = self.serializer_class(data=data)
            if serializer.is_valid(raise_exception=True):
                CalendarSlot.objects.create(**serializer.validated_data)

        return CustomResponse({"message": Success.UNAVAILABILITY_SET}, status=201)
