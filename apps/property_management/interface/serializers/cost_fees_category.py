from rest_framework import serializers

from apps.property_management.infrastructure.models import CostFeesCategory


class CostFeesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFeesCategory
        fields = '__all__'
