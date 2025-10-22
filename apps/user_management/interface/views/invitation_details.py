from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import TenantInvitation, VendorInvitation
from apps.user_management.interface.serializers import InvitationAcceptanceSerializer, InvitationDetailSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class InvitationDetailsView(APIView):
    """
    API view to get invitation details by invitation ID without authentication.
    Supports both vendor and tenant invitations based on boolean flags.

    URL: GET /v1/api/invitation-details/{invitation_id}/?vendor=true&tenant=false
    """

    permission_classes = []

    def get(self, request, invitation_id):
        """
        Get invitation details using invitation ID and type flags.

        Query Parameters:
        - vendor (boolean): Set to true to fetch vendor invitation details
        - tenant (boolean): Set to true to fetch tenant invitation details

        Returns:
        - Invitation details including basic info, sender info, and type-specific details
        """
        vendor = request.query_params.get('vendor', '').lower() == 'true'
        tenant = request.query_params.get('tenant', '').lower() == 'true'

        if not vendor and not tenant:
            return CustomResponse({"error": Error.INVALID_INVITATION_TYPE}, status=status.HTTP_400_BAD_REQUEST)

        invitation = None

        # Try to fetch vendor invitation if vendor=true
        if vendor:
            try:
                invitation = VendorInvitation.objects.get(id=invitation_id)
            except VendorInvitation.DoesNotExist:
                if not tenant:  # If only vendor was requested and not found
                    return CustomResponse({"error": Error.INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Try to fetch tenant invitation if tenant=true and vendor invitation not found
        if tenant and invitation is None:
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse({"error": Error.INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if invitation is None:
            return CustomResponse({"error": Error.INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse({"error": Error.INVITATION_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InvitationDetailSerializer(invitation)

        return CustomResponse({"message": Success.INVITATION_DETAILS_RETRIEVED, "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Accept or reject invitation using invitation ID and type flags from payload.
        Note: invitation_id from URL is ignored, only payload invitation_id is used.

        Payload:
        - invitation_id (integer): The invitation ID to update
        - accept (boolean): True to accept, False to reject the invitation
        - vendor (boolean): Set to true for vendor invitation
        - tenant (boolean): Set to true for tenant invitation

        Returns:
        - Success message with updated invitation status
        """
        serializer = InvitationAcceptanceSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        invitation_id = validated_data['invitation_id']
        accept = validated_data['accept']
        vendor = validated_data.get('vendor', False)
        tenant = validated_data.get('tenant', False)

        invitation = None
        if vendor:
            try:
                invitation = VendorInvitation.objects.get(id=invitation_id)
            except VendorInvitation.DoesNotExist:
                return CustomResponse({"error": Error.VENDOR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        elif tenant:
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse({"error": Error.TENANT_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse({"error": Error.INVITATION_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

        if invitation.accepted and accept:
            return CustomResponse({"error": Error.INVITATION_ALREADY_ACCEPTED}, status=status.HTTP_400_BAD_REQUEST)

        invitation.accepted = accept
        invitation.save(update_fields=['accepted', 'updated_at'])

        # If tenant invitation is accepted, mark the assigned unit/property as occupied
        if accept and hasattr(invitation, 'assignment_type'):
            assigned_obj = invitation.assigned_object
            if assigned_obj:
                assigned_obj.status = 'occupied'
                assigned_obj.save(update_fields=['status'])

        if accept:
            message = Success.INVITATION_ACCEPTED
        else:
            message = Success.INVITATION_REJECTED

        return CustomResponse({"message": message}, status=status.HTTP_200_OK)
