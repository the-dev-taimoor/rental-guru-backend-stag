from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.properties.infrastructure.models import CostFee, CostFeesCategory, Property
from apps.properties.utils import cost_fee_options
from common.constants import Error, Success
from common.utils import CustomResponse, NotFound


class CostFeeTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        unit_id = request.query_params.get('unit', None)
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)

        try:
            filtered_options = self.get_filtered_cost_fee_options(property_id, unit_id)

            return CustomResponse({"data": filtered_options, "message": Success.COST_FEE_TYPES}, status=status.HTTP_200_OK)
        except Exception as e:
            return CustomResponse({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def get_filtered_cost_fee_options(self, property_id, unit_id):
        cost_fee_categories = CostFeesCategory.objects.filter(property_id=property_id, unit_id=unit_id)

        existing_fees = set(CostFee.objects.filter(category__in=cost_fee_categories).values_list('fee_name', flat=True))

        # Get property type to determine which cost fee options to use
        try:
            property_obj = Property.objects.get(id=property_id)
            property_type = property_obj.property_type
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        # Use property-specific options if available, otherwise use 'others'
        property_cost_options = cost_fee_options.get(property_type, cost_fee_options.get('others', {}))

        filtered_cost_fee_options = {}
        for category, fee_names in property_cost_options.items():
            filtered_cost_fee_options[category] = [fee for fee in fee_names if fee not in existing_fees]

        return filtered_cost_fee_options
