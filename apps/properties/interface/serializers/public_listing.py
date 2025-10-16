from apps.properties.infrastructure.models import ListingInfo
from rest_framework import serializers

class PublicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingInfo
        fields = '__all__'
