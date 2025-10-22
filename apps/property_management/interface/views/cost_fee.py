from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.property_management.infrastructure.models import CostFee, CostFeeCategory, Property
from apps.property_management.interface.serializers import CostFeeRetrieveSerializer, CostFeesCategorySerializer, CostFeeSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class CostFeeViewSet(APIView):
    permission_classes = [IsAuthenticated]
    queryset = CostFeeCategory.objects.all()
    serializer_class = CostFeesCategorySerializer

    def post(self, request):
        updated_call = False
        data = request.data.copy()
        unit = data.get('unit')
        cost_fees = data.pop('cost_fees')
        property_ = data.pop('property')
        page_saved = data.get('page_saved')
        if not page_saved:
            raise ValidationError(Error.PAGE_SAVED_REQUIRED)

        self.check_fee_id_exists_update_case(cost_fees, property_, unit)
        self.check_fee_exists_create_case(cost_fees, property_, unit)

        all_data = list()

        for cost_fee in cost_fees:
            category_data = dict()
            parent_data = dict()
            category_name = cost_fee.get('category_name')
            parent_data['unit'] = unit
            parent_data['property'] = property_
            parent_data['category_name'] = category_name

            existing_category = CostFeeCategory.objects.filter(property=property_, unit=unit, category_name=category_name).first()

            if existing_category:
                category = existing_category
            else:
                serializer = self.serializer_class(data=parent_data)
                serializer.is_valid(raise_exception=True)
                category = CostFeeCategory.objects.create(**serializer.validated_data)

            category_data['category_name'] = category_name

            fees_data = list()
            fees = cost_fee.get('fees')

            for fee in fees:
                fee_id = fee.get('id')
                if fee_id:
                    self.perform_custom_update(fee_id, fee, fees_data)
                    updated_call = True
                else:
                    self.perform_custom_create(category, fee, fees_data)

            category_data['fees'] = fees_data
            all_data.append(category_data)

        try:
            property_obj = Property.objects.get(id=property_)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        if not updated_call:
            property_obj.page_saved = page_saved
            property_obj.save(update_fields=['page_saved'])

        return CustomResponse({'message': Success.COST_FEE_ADDED, 'data': all_data})

    def check_fee_id_exists_update_case(self, cost_fees, property_, unit):
        existing_fees_ids = [f.get('id') for c in cost_fees for f in c.get('fees') if f.get('id')]
        existing_fees = CostFee.objects.filter(id__in=existing_fees_ids, category__property=property_, category__unit=unit)

        # Check if all IDs from payload exist in database
        db_fee_ids = set(existing_fees.values_list('id', flat=True))
        missing_ids = set(existing_fees_ids) - db_fee_ids

        if missing_ids:
            raise ValidationError(Error.COST_FEE_ID_NOT_FOUND.format(', '.join(map(str, missing_ids))))

    def check_fee_exists_create_case(self, cost_fees, property_id, unit_id):
        for cost_fee in cost_fees:
            category_name = cost_fee.get('category_name')
            fees = cost_fee.get('fees')
            for fee in fees:
                if not fee.get('id'):
                    if CostFee.objects.filter(
                        category__property=property_id,
                        category__unit=unit_id,
                        category__category_name=category_name,
                        fee_name=fee.get('fee_name'),
                    ).exists():
                        raise ValidationError(Error.COST_FEE_NAME_EXISTS.format(fee.get('fee_name')))

    def perform_custom_update(self, fee_id, fee, fees_data):
        try:
            existing_fee = CostFee.objects.get(id=fee_id)
        except CostFee.DoesNotExist:
            raise NotFound(Error.COST_FEE_ID_NOT_FOUND.format(fee_id))

        for field, value in fee.items():
            if field not in ['id', 'category']:
                setattr(existing_fee, field, value)
        existing_fee.save()
        fee_serializer = CostFeeRetrieveSerializer(existing_fee)
        fees_data.append(fee_serializer.data)

    def perform_custom_create(self, category, fee, fees_data):
        fee['category'] = category.id
        fee_serializer = CostFeeSerializer(data=fee)
        fee_serializer.is_valid(raise_exception=True)
        new_fee_instance = CostFee.objects.create(**fee_serializer.validated_data)

        response_serializer = CostFeeRetrieveSerializer(new_fee_instance)
        fees_data.append(response_serializer.data)
