from rest_framework import serializers

from common.constants import Error
from apps.properties.infrastructure.models import RentDetails

class RentDetailsSerializer(serializers.ModelSerializer):
    page_saved = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = RentDetails
        fields = '__all__'

    def create(self, validated_data):
        page_saved = validated_data.pop('page_saved')
        rental = super().create(validated_data)
        if validated_data.get('unit'):
            obj = rental.unit
        else:
            obj = rental.property
        obj.page_saved = page_saved
        obj.save(update_fields=['page_saved'])
        return rental

    def validate(self, data):
        unit = data.get('unit')

        is_update = self.instance is not None
        if not is_update:
            if RentDetails.objects.filter(property=data['property'], unit=unit).exists():
                raise serializers.ValidationError(Error.RENT_DETAILS_EXISTS)

        if data.get('assigned_tenant'):
            if data.get('promote_special_offer'):
                raise serializers.ValidationError(Error.OFFER_NOT_REQUIRED)
            else:
                if not (data.get('lease_start_date') and data.get('lease_end_date')):
                    raise serializers.ValidationError(
                        Error.TENANT_FIELDS_REQUIRED.format("'lease_start_date', 'lease_end_date'"))
        else:
            if data.get('promote_special_offer'):
                if not (data.get('offer_start_date') and data.get('offer_end_date') and data.get('offer_percentage')):
                    raise serializers.ValidationError(Error.OFFER_REQUIRED.format("'offer_start_date', 'offer_end_date', 'offer_percentage'"))
        return data