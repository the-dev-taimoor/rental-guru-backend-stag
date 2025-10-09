from rest_framework import serializers

from apps.properties.infrastructure.models import CostFee

class CostFeeRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFee
        fields = ['id', 'fee_name', 'payment_frequency', 'fee_amount', 'fee_type', 'is_required', 'refundable_status', 'category']
