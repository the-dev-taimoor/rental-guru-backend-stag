from rest_framework import serializers

from apps.user_management.infrastructure.models import PropertyOwner
from common.utils import get_presigned_url


class PropertyOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwner
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.profile_image_path.name:
            rep["profile_image_path"] = get_presigned_url(instance.profile_image_path.name)
        return rep
