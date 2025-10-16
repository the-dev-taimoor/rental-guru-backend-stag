from rest_framework import serializers

from apps.properties.infrastructure.models import PropertyPhoto, ListingInfo
from .property_photo import PropertyPhotoSerializer

class ListingInfoRetrieveSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = ListingInfo
        exclude = ['created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(property=instance.property, unit__isnull=True)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation