from django.utils import timezone
from rest_framework import serializers

from apps.user_management.infrastructure.models import Agreement
from common.utils import get_presigned_url


class InvitationDetailsSerializer(serializers.Serializer):
    """
    Unified serializer for both vendor and tenant invitation details.
    Returns invitation information without requiring authentication.
    """

    def to_representation(self, instance):
        """
        Convert invitation instance to dictionary representation.
        Handles both VendorInvitation and TenantInvitation models.
        """
        if hasattr(instance, 'role'):  # VendorInvitation
            return {
                'id': instance.id,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'sender': instance.sender.email,
                'sender_name': f"{instance.sender.first_name} {instance.sender.last_name}".strip(),
                'expired_at': instance.expired_at,
            }
        elif hasattr(instance, 'tenant_type'):  # TenantInvitation
            lease_agreement_url = None
            agreement = Agreement.objects.filter(invitation=instance.id).order_by('-created_at').first()
            if agreement.lease_agreement and agreement.lease_agreement.name:
                lease_agreement_url = get_presigned_url(agreement.lease_agreement.name)

            return {
                'id': instance.id,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'sender': instance.sender.email,
                'sender_name': f"{instance.sender.first_name} {instance.sender.last_name}".strip(),
                'lease_start_date': instance.lease_start_date,
                'lease_end_date': instance.lease_end_date,
                'lease_agreement_url': lease_agreement_url,
                'lease_ended': True if instance.lease_end_date <= timezone.now().date() else False,
                'expired_at': instance.expired_at,
            }
        else:
            return {}
