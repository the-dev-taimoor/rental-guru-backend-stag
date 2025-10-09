from rest_framework import serializers
from common.utils import get_presigned_url
from apps.user_authentication.infrastructure.models import KYCRequest


class KYCVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCRequest
        fields = ['user_id', 'id_type', 'front_image', 'back_image', 'notes']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.front_image.name:
            rep["front_image"] = get_presigned_url(instance.front_image.name)
        if instance.back_image.name:
            rep["back_image"] = get_presigned_url(instance.back_image.name)
        return rep

    def validate_user_id(self, value):
        try:
            existing_kyc = KYCRequest.objects.get(user_id=value)
            if existing_kyc.status == 'rejected':
                existing_kyc.delete()
            else:
                raise serializers.ValidationError("You have already submitted a KYC request.")
        except KYCRequest.DoesNotExist:
            pass
        return value