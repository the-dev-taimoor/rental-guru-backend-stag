from rest_framework import serializers

from apps.properties.infrastructure.models import Property, PropertyPhoto

from .property_photo import PropertyPhotoSerializer


class PropertyRetrieveSerializer(serializers.ModelSerializer):
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Property
        exclude = ['property_owner', 'created_at', 'updated_at']

    def get_photos(self, obj):
        # Only get photos that don't belong to any unit (unit is null)
        photos = PropertyPhoto.objects.filter(property=obj.id, unit__isnull=True)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        return photos_data
