from rest_framework import serializers

from apps.properties.infrastructure.models import ListingInfo


class PublicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingInfo
        fields = '__all__'
