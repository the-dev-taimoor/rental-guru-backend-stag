from rest_framework import serializers
from common.constants import Error

class InvitationAgreementSerializer(serializers.Serializer):
    """
    Serializer for updating invitation agreement status and signed agreement file.
    """
    invitation_id = serializers.IntegerField(required=True)
    agreed = serializers.BooleanField(required=True)
    signed_agreement = serializers.FileField(required=True)

    def validate_agreed(self, value):
        if value is not True:
            raise serializers.ValidationError(Error.AGREEMENT_REQUIRED)
        return value