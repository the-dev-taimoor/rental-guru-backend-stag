from rest_framework import serializers

from apps.user_management.infrastructure.models import VendorInvitation


class VendorInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorInvitation
        fields = ['first_name', 'last_name', 'email', 'role']
