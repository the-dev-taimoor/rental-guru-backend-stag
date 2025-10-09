from rest_framework import serializers

class VendorInvitationBlockSerializer(serializers.Serializer):
    invitation_id = serializers.IntegerField(required=True)
    blocked = serializers.BooleanField(required=True)
