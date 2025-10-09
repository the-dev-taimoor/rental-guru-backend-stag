from rest_framework import serializers

from .listing_info import ListingInfoSerializer

class ListingInfoUpdateSerializer(ListingInfoSerializer):
    existing_photos = serializers.JSONField(write_only=True, required=False)

    def validate(self, data):
        return data