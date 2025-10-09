from rest_framework import serializers
from common.utils import get_presigned_url
from apps.user_authentication.infrastructure.models import PropertyOwner
                                                            
class PropertyOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwner
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.profile_image_path.name:
            rep["profile_image_path"] = get_presigned_url(instance.profile_image_path.name)
        return rep