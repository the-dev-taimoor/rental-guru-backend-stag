from rest_framework import serializers
from common.utils import get_presigned_url

from apps.properties.infrastructure.models import PropertyPhoto

class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ['id', 'photo']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.photo.name:
            rep["photo"] = get_presigned_url(instance.photo.name)
        return rep