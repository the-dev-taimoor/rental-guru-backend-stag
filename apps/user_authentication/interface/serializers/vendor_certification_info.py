from rest_framework import serializers
from common.utils import get_presigned_url
from apps.user_authentication.infrastructure.models import Vendor

class VendorCertificationInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor certification information tab"""

    class Meta:
        model = Vendor
        fields = ['insurance_coverage', 'emergency_contact']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.insurance_certificates.name:
            rep["insurance_certificates"] = get_presigned_url(instance.insurance_certificates.name)
        if instance.other_certificates.name:
            rep["other_certificates"] = get_presigned_url(instance.other_certificates.name)
        return rep