from rest_framework import serializers

from apps.property_management.infrastructure.models import RentDetails


class RentDetailsRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentDetails
        exclude = ['created_at', 'updated_at']
