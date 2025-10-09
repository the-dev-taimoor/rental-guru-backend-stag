from rest_framework import serializers

from apps.properties.infrastructure.models import PropertyPhoto, Unit
from .property_photo import PropertyPhotoSerializer

class UnitRetrieveSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False)

    class Meta:
        model = Unit
        exclude = ['property', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(unit=instance.id)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation