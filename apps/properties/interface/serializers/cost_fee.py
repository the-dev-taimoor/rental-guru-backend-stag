from rest_framework import serializers

from apps.properties.infrastructure.models import CostFee
from common.constants import Error


class CostFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFee
        fields = '__all__'

    def validate(self, data):
        if CostFee.objects.filter(**data).exists():
            raise serializers.ValidationError(Error.COST_FEE_EXISTS)
        return data
