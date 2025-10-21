from rest_framework import serializers

from apps.user_management.infrastructure.models import KYCRequest
from common.utils import get_presigned_url


class KYCRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCRequest
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.front_image.name:
            rep["front_image"] = get_presigned_url(instance.front_image.name)
        if instance.back_image.name:
            rep["back_image"] = get_presigned_url(instance.back_image.name)
        return rep
