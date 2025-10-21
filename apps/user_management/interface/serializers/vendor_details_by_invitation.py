from rest_framework import serializers

from apps.user_management.infrastructure.models import VendorInvitation

from .vendor_basic_info import VendorBasicInfoSerializer
from .vendor_business_info import VendorBusinessInfoSerializer
from .vendor_certification_info import VendorCertificationInfoSerializer
from .vendor_jobs_info import VendorJobsInfoSerializer
from .vendor_payments_info import VendorPaymentsInfoSerializer
from .vendor_services_info import VendorServicesInfoSerializer


class VendorDetailsByInvitationSerializer(serializers.Serializer):
    """Main serializer that combines all vendor information tabs"""

    invitation_info = serializers.SerializerMethodField()
    basic_info = VendorBasicInfoSerializer(read_only=True)
    business_info = VendorBusinessInfoSerializer(read_only=True)
    services_info = VendorServicesInfoSerializer(read_only=True)
    certification_info = VendorCertificationInfoSerializer(read_only=True)
    jobs_info = VendorJobsInfoSerializer(read_only=True)
    payments_info = VendorPaymentsInfoSerializer(read_only=True)

    def get_invitation_info(self, obj):
        invitation = obj.get('invitation')
        if invitation:
            return {
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'role': invitation.role,
                'role_display': dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(invitation.role, invitation.role),
                'accepted': invitation.accepted,
                'blocked': invitation.blocked,
                'created_at': invitation.created_at,
                'updated_at': invitation.updated_at,
            }
        return None
