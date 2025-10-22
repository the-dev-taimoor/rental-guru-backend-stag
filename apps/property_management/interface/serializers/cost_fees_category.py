from rest_framework import serializers

from apps.property_management.infrastructure.models import CostFeeCategory


class CostFeesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFeeCategory
        fields = '__all__'
