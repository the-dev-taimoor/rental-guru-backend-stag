from datetime import timedelta
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.filters import OrderingFilter

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model

from common.constants import Success, Error
from common.filters import CustomSearchFilter
from common.utils import CustomResponse, send_email_

from apps.user_authentication.infrastructure.models import Vendor, VendorInvitation
from apps.user_authentication.interface.serializers import VendorInvitationSerializer
from apps.user_authentication.application.pagination import VendorInvitationPagination


class VendorInvitationView(APIView):
    """
    API view to send vendor invitations.
    Accepts first_name, last_name, email, and role in the payload.
    Supports search functionality for vendor name, email, and role.
    """
    queryset = VendorInvitation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorInvitationSerializer
    filter_backends = [DjangoFilterBackend, CustomSearchFilter, OrderingFilter]
    filterset_fields = ['role', 'accepted', 'blocked']
    search_fields = ['first_name', 'last_name', 'email', 'role']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        return self.queryset.filter(sender=self.request.user).order_by('-created_at')

    def filter_queryset(self, queryset):
        """Apply filters to queryset"""
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def post(self, request):
        """
        Send vendor invitation email and save invitation record.
        Expected payload:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "role": "electrical_services"
        }
        """
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email')
        role = request.data.get('role')
        role_display = dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(role, role)

        if Vendor.objects.filter(user_id__email=email).exists():
            return CustomResponse({"error": Error.VENDOR_ALREADY_EXISTS}, status=status.HTTP_400_BAD_REQUEST)

        if VendorInvitation.objects.filter(email=email, sender=request.user, role=role).exists():
            if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, accepted=True).exists():
                return CustomResponse({"error": Error.VENDOR_INVITATION_ALREADY_ACCEPTED.format(email, role)},
                                      status=status.HTTP_400_BAD_REQUEST)
            if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__gte=timezone.now()).exists():
                return CustomResponse({"error": Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role)},
                                      status=status.HTTP_400_BAD_REQUEST)
            if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False).exists():
                VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False).delete()


        if not serializer.is_valid():
            if 'must make a unique set' in str(serializer.errors):
                return CustomResponse(
                    {"error": Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role_display)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        email = validated_data['email']
        role = validated_data['role']

        try:
            invitation = VendorInvitation.objects.create(
                sender=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                expired_at=timezone.now() + timedelta(days=5)
            )

            email_variables = {
                'VENDOR_FIRST_NAME': first_name,
                'VENDOR_LAST_NAME': last_name,
                'VENDOR_ROLE': role,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?vendor=true&invitation_id={invitation.id}"
            }

            send_email_(email, email_variables, 'INVITE-VENDOR')

            response_data = {
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'role': invitation.role,
                'created_at': invitation.created_at
            }

            return CustomResponse(
                {
                    "message": Success.VENDOR_INVITATION_SENT,
                    "data": response_data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Handle IntegrityError for duplicate invitations
            if 'UNIQUE constraint failed' in str(e) or 'duplicate key value' in str(e):
                role_display = dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(role, role)
                return CustomResponse(
                    {"error": Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role_display)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_SEND_FAILED.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        paginator = VendorInvitationPagination()
        result_page = paginator.paginate_queryset(filtered_queryset, request)

        invitation_data = []
        for invitation in result_page:
            invitation_data.append({
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'role': invitation.role,
                'accepted': invitation.accepted,
                'blocked': invitation.blocked,
                'created_at': invitation.created_at
            })

        return paginator.get_paginated_response(invitation_data)

    def delete(self, request, invitation_id):
        """
        Delete a vendor invitation and the user account if they have joined.
        URL: DELETE /v1/api/user-authentication/invite-vendor/{invitation_id}/
        """
        try:
            invitation = VendorInvitation.objects.get(id=invitation_id, sender=request.user)
        except VendorInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            email = invitation.email

            try:
                user = get_user_model().objects.get(email=email)
                user.delete()
            except get_user_model().DoesNotExist:
                pass

            invitation.delete()

            return CustomResponse(
                {
                    "message": Success.VENDOR_INVITATION_DELETED,
                    "data": {
                        "invitation_id": invitation_id,
                        "email": email,
                        "deleted": True
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_DELETE_FAILED.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request):
        """
        Block/unblock a vendor invitation if user exists.

        Expected payload:
        {
            "invitation_id": 1,
            "blocked": true
        }
        """
        invitation_id = request.data.get('invitation_id')
        blocked = request.data.get('blocked')

        if invitation_id is None:
            return CustomResponse({"error": Error.INVITATION_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        if blocked is None:
            return CustomResponse({"error": Error.BLOCKED_FIELD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invitation = VendorInvitation.objects.get(id=invitation_id, sender=request.user)
        except VendorInvitation.DoesNotExist:
            return CustomResponse({"error": Error.VENDOR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        try:
            invitation.blocked = blocked
            invitation.save()

            try:
                user = get_user_model().objects.get(email=invitation.email)
                user.is_ban = blocked
                user.save()
            except get_user_model().DoesNotExist:
                pass

            message = Success.VENDOR_INVITATION_BLOCKED if blocked else Success.VENDOR_INVITATION_UNBLOCKED

            return CustomResponse(
                {
                    "message": message,
                    "data": {
                        "id": invitation.id,
                        "email": invitation.email,
                        "blocked": invitation.blocked
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_BLOCK_FAILED.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

