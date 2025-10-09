from rest_framework import serializers
from common.constants import Error

class InvitationAcceptanceSerializer(serializers.Serializer):
    """
    Serializer for accepting or rejecting invitations.
    """
    invitation_id = serializers.IntegerField(required=True)
    accept = serializers.BooleanField(required=True)
    vendor = serializers.BooleanField(required=False, default=False)
    tenant = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        vendor = attrs.get('vendor', False)
        tenant = attrs.get('tenant', False)

        if not vendor and not tenant:
            raise serializers.ValidationError(Error.INVITATION_TYPE_REQUIRED)

        if vendor and tenant:
            raise serializers.ValidationError(Error.INVALID_INVITATION_TYPE)

        return attrs