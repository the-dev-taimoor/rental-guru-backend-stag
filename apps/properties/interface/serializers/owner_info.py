from rest_framework import serializers

from apps.properties.infrastructure.models import OwnerInfo

class OwnerInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = OwnerInfo
        fields = '__all__'
