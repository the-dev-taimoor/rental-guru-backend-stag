from rest_framework import serializers

from apps.property_management.infrastructure.models import RentDetail


class RentDetailRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentDetail
        exclude = ['created_at', 'updated_at']
