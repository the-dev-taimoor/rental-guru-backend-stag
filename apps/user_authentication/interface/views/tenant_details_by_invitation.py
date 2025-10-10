
from rest_framework.views import APIView
from rest_framework import status, permissions

from django.utils import timezone
from django.contrib.auth import get_user_model

from common.constants import Success, Error
from common.utils import CustomResponse, get_presigned_url

from apps.user_authentication.infrastructure.models import Agreements, TenantInvitation


class TenantDetailsByInvitationView(APIView):
    """
    API view to get tenant details by invitation ID.
    Returns tenant information organized in different sections.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invitation_id):
        """
        Get tenant details using invitation ID.

        Returns:
        - basic_info: Tenant basic information (name, contact, etc.)
        - lease_info: Lease details and property information
        """
        try:
            invitation = TenantInvitation.objects.get(id=invitation_id, sender=request.user)
        except TenantInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.TENANT_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invitation.accepted:
            return CustomResponse(
                {"error": Error.TENANT_INVITATION_NOT_ACCEPTED},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = get_user_model().objects.get(email=invitation.email)
        except get_user_model().DoesNotExist:
            return CustomResponse(
                {"error": Error.TENANT_NOT_FOUND_FOR_INVITATION},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            'basic_info': self._get_basic_info(user, invitation),
            'lease_info': self._get_lease_info(invitation),
        }

        return CustomResponse(
            {
                "message": Success.TENANT_DETAILS_RETRIEVED,
                "data": response_data
            },
            status=status.HTTP_200_OK
        )

    def _get_basic_info(self, user, invitation):
        """Get basic user information"""
        assigned_obj = invitation.assigned_object
        assignment_name = ""
        assignment_address = ""

        if assigned_obj:
            if invitation.assignment_type == 'property':
                assignment_name = assigned_obj.name
                assignment_address = assigned_obj.street_address
            elif invitation.assignment_type == 'unit':
                assignment_name = f"{assigned_obj.number} - {assigned_obj.property.name}"
                assignment_address = assigned_obj.property.street_address

        return {
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'phone_number': user.phone_number or "Not provided",
            'email': user.email,
            'assignment_type': invitation.assignment_type,
            'assignment_name': assignment_name,
            'assignment_address': assignment_address,
        }

    def _get_lease_info(self, invitation):
        """Get lease and property information"""
        lease_agreement_url = None
        agreement = Agreements.objects.filter(invitation=invitation.id).order_by('-created_at').first()
        if agreement.lease_agreement and agreement.lease_agreement.name:
            lease_agreement_url = get_presigned_url(agreement.lease_agreement.name)

        return {
            'lease_amount': invitation.lease_amount,
            'security_deposit': invitation.security_deposit,
            'lease_start_date': invitation.lease_start_date,
            'lease_end_date': invitation.lease_end_date,
            'lease_agreement_url': lease_agreement_url,
            'lease_ended': True if invitation.lease_end_date <= timezone.now().date() else False
        }

