from rest_framework import serializers

from apps.user_authentication.infrastructure.models import Vendor
from common.utils import get_presigned_url


class VendorBusinessInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor business information tab"""

    class Meta:
        model = Vendor
        fields = [
            'business_name',
            'business_website',
            'business_address',
            'business_type',
            'company_registration_number',
            'registration_type',
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.business_license.name:
            rep["business_license"] = get_presigned_url(instance.business_license.name)
        return rep
