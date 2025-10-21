from rest_framework import serializers


class ResendInvitationSerializer(serializers.Serializer):
    invitation_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(choices=['vendor', 'tenant'], required=True)
