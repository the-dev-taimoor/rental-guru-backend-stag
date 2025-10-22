from rest_framework import serializers

from apps.property_management.infrastructure.models import CostFeeCategory


class CostFeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFeeCategory
        fields = '__all__'
