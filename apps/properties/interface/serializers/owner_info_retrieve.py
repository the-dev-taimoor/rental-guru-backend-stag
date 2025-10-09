from rest_framework import serializers

from apps.properties.infrastructure.models import OwnerInfo

class OwnerInfoRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = OwnerInfo
        fields = ['id', 'email', 'percentage', 'emergency_person', 'emergency_contact', 'registered']