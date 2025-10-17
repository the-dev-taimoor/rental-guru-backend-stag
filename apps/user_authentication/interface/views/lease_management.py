from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.user_authentication.infrastructure.models import Agreements, TenantInvitation
from apps.user_authentication.interface.serializers import LeaseManagementSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class LeaseManagementView(APIView):
    """
    API view to manage lease agreements (end or renew).
    Takes invitation_id and action (end/renew) to either end the lease or extend it.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeaseManagementSerializer

    def put(self, request):
        """
        Manage a lease agreement (end or renew).

        Expected payload:
        if action is end:
        {
            "invitation_id": 1,
            "action": "end"
        }
        If action is renew, additional fields are required:
        {
            "invitation_id": 1,
            "action": "renew",
            "lease_start_date": "2025-02-01",
            "lease_end_date": "2026-02-01",
            "rent_amount": 2000,
            "security_deposit": 4000,
            "lease_agreement": <file>
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return CustomResponse({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        invitation_id = serializer.validated_data['invitation_id']
        action = serializer.validated_data['action']

        try:
            invitation = TenantInvitation.objects.get(id=invitation_id, sender=request.user)
        except TenantInvitation.DoesNotExist:
            return CustomResponse({"error": Error.TENANT_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        try:
            if action == 'end':
                if not invitation.accepted:
                    return CustomResponse({"error": Error.LEASE_NOT_ACTIVE}, status=status.HTTP_400_BAD_REQUEST)
                if invitation.lease_end_date < timezone.now().date():
                    return CustomResponse({"error": Error.LEASE_ALREADY_ENDED}, status=status.HTTP_400_BAD_REQUEST)
                # End lease scenario
                # Block the tenant invitation
                with transaction.atomic():
                    invitation.blocked = True
                    invitation.lease_end_date = timezone.now().date()
                    invitation.save(update_fields=['blocked', 'lease_end_date', 'updated_at'])

                    # Make the assigned property/unit vacant
                    assigned_obj = invitation.assigned_object
                    if assigned_obj:
                        assigned_obj.status = 'vacant'
                        assigned_obj.save(update_fields=['status'])

                return CustomResponse({"message": Success.LEASE_ENDED_SUCCESSFULLY}, status=status.HTTP_200_OK)

            elif action == 'renew':
                # Renew lease scenario
                # Update the lease end date
                with transaction.atomic():
                    invitation.lease_end_date = serializer.validated_data.get('lease_end_date')
                    invitation.lease_amount = serializer.validated_data['rent_amount']
                    invitation.security_deposit = serializer.validated_data.get('security_deposit', invitation.security_deposit)
                    invitation.lease_start_date = serializer.validated_data['lease_start_date']
                    invitation.agreed = False
                    invitation.save(
                        update_fields=['lease_start_date', 'lease_end_date', 'lease_amount', 'security_deposit', 'agreed', 'updated_at']
                    )
                    Agreements.objects.create(invitation=invitation, lease_agreement=serializer.validated_data['lease_agreement'])

                return CustomResponse({"message": Success.LEASE_RENEWED_SUCCESSFULLY}, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = Error.LEASE_END_FAILED if action == 'end' else Error.LEASE_RENEWAL_FAILED
            return CustomResponse({"error": error_message.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
