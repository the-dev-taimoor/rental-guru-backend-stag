from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.user_authentication.infrastructure.models import TenantInvitation, VendorInvitation
from apps.user_authentication.interface.serializers import ResendInvitationSerializer
from common.constants import Error, Success
from common.utils import CustomResponse, send_email_


class ResendInvitation(APIView):
    """
    API view to resend invitation to a vendor or tenant.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Resend invitation to a vendor or tenant.

        Payload:
        - invitation_id (integer): The invitation ID to resend
        - role (string): The role of the invitation (vendor/tenant)

        Returns:
        - Success message with updated invitation status
        """
        serializer = ResendInvitationSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        invitation_id = validated_data['invitation_id']
        role = validated_data.get('role', 'vendor')

        invitation = None
        if role == 'vendor':
            try:
                invitation = VendorInvitation.objects.get(id=invitation_id)
            except VendorInvitation.DoesNotExist:
                return CustomResponse({"error": Error.VENDOR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        elif role == 'tenant':
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse({"error": Error.TENANT_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if invitation.accepted:
            return CustomResponse({"error": Error.INVITATION_ALREADY_ACCEPTED}, status=status.HTTP_400_BAD_REQUEST)

        # Resend invitation email
        if role == 'vendor':
            variables = {
                'VENDOR_FIRST_NAME': invitation.first_name,
                'VENDOR_LAST_NAME': invitation.last_name,
                'VENDOR_ROLE': invitation.role,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?vendor=true&invitation_id={invitation.id}",
            }
            send_email_(invitation.email, variables, 'INVITE-VENDOR')
        elif role == 'tenant':
            variables = {
                'TENANT_FIRST_NAME': invitation.first_name,
                'OWNER_NAME': invitation.sender.first_name,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?tenant=true&invitation_id={invitation.id}",
            }
            send_email_(invitation.email, variables, 'INVITE-TENANT')

        invitation.expired_at = timezone.now() + timedelta(days=5)
        invitation.save(update_fields=['expired_at'])

        return CustomResponse({"message": Success.INVITATION_RESENT}, status=status.HTTP_200_OK)
