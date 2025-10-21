from rest_framework import serializers

from apps.property_management.infrastructure.models import OwnerInfo


class OwnerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerInfo
        fields = '__all__'
