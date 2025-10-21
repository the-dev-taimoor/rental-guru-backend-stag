import logging

from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.property_management.infrastructure.models import OwnerInfo
from apps.user_management.application.services.otp import otp_email
from apps.user_management.infrastructure.models import KYCRequest, PropertyOwner, Tenant, TenantInvitation, Vendor, VendorInvitation
from apps.user_management.interface.serializers import (
    InvitationDetailsSerializer,
    PropertyOwnerProfileSerializer,
    TenantProfileSerializer,
    UserSerializer,
    VendorProfileSerializer,
)
from common.constants import Error, Success
from common.utils import CustomResponse

logger = logging.getLogger('django')


class SignupView(APIView):
    parser_classes = [JSONParser]

    def get(self, request, *args, **kwargs):
        """
        Retrieve details of the authenticated user including roles, profiles, and KYC request.
        """
        user = request.user
        if not user.is_authenticated:
            raise NotAuthenticated(Error.USER_NOT_AUTHENTICATED)

        roles = user.role_user.values_list('role', flat=True)
        property_owner_profile = None
        vendor_profile = None
        tenant_profile = None
        kyc_request = None

        invitations = []

        if 'property_owner' in roles:
            try:
                property_owner_profile = PropertyOwner.objects.get(user_id=user)
            except PropertyOwner.DoesNotExist:
                pass
        if 'vendor' in roles:
            try:
                vendor_profile = Vendor.objects.get(user_id=user)
            except Vendor.DoesNotExist:
                pass
        if 'tenant' in roles:
            try:
                tenant_profile = Tenant.objects.get(user_id=user)
            except Tenant.DoesNotExist:
                pass
        try:
            vendor_invitations = VendorInvitation.objects.get(email=user.email, accepted=True)
            data_ = InvitationDetailsSerializer(vendor_invitations).data
            data_['role'] = 'vendor'
            invitations.append(data_)
        except Exception as e:
            logger.error(f"Exception occured while inviting vendor: {str(e)}")
            pass
        try:
            tenant_invitations = TenantInvitation.objects.get(email=user.email, accepted=True)
            data_ = InvitationDetailsSerializer(tenant_invitations).data
            data_['role'] = 'tenant'
            invitations.append(data_)
        except Exception as e:
            logger.error(f"Exception occured while inviting tenant: {str(e)}")
            pass

        try:
            kyc_request = KYCRequest.objects.filter(user_id=user).values('id', 'id_type', 'status', 'created_at', 'review_notes').first()
        except KYCRequest.DoesNotExist:
            pass

        response_data = {
            'data': {
                'user': UserSerializer(user).data,
                'kyc_request': kyc_request if kyc_request else None,
                'roles': list(roles),
                'property_owner_profile': PropertyOwnerProfileSerializer(property_owner_profile).data if property_owner_profile else None,
                'vendor_profile': VendorProfileSerializer(vendor_profile).data if vendor_profile else None,
                'tenant_profile': TenantProfileSerializer(tenant_profile).data if tenant_profile else None,
                'invitations': invitations,
            },
            'message': 'User details.',
        }
        return CustomResponse(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: Success.USER_CREATED,
            400: "custom user with this email already exists.",
        },
    )
    @csrf_exempt
    def post(self, request):
        """
        Register a new user with provided data and send a signup OTP email.
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                user = serializer.save()

                invitation_id = serializer.validated_data.get('invitation_id')
                invitation_role = serializer.validated_data.get('invitation_role')
                if invitation_id and invitation_role:
                    self.accept_invitation(user, invitation_id, invitation_role)

                # Update any existing OwnerInfo records with this email to mark them as registered
                try:
                    OwnerInfo.objects.filter(email=user.email, registered=False).update(registered=True)
                except Exception as e:
                    # Log the error but don't interrupt the signup flow
                    logger.error(f"Error updating OwnerInfo records: {str(e)}")

            refresh_token = None
            access_token = None
            if not invitation_id:
                otp_email(user, action='SIGNUP')
            else:
                # Generate token
                refresh = RefreshToken.for_user(user)
                refresh_token = str(refresh)
                access_token = str(refresh.access_token)

            user_data = UserSerializer(user).data
            user_data['refresh_token'] = refresh_token
            user_data['access_token'] = access_token

            response_data = {"data": user_data, "error": None, "success": True, "message": Success.USER_CREATED}
            return CustomResponse(response_data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

    def accept_invitation(self, user, invitation_id, invitation_role):
        """
        Accept an invitation using invitation ID.
        """
        model = VendorInvitation
        try:
            if invitation_role == 'vendor':
                model = VendorInvitation
            if invitation_role == 'tenant':
                model = TenantInvitation

            invitation = model.objects.get(id=invitation_id)
            if invitation.accepted:
                raise ValidationError(Error.INVITATION_ALREADY_ACCEPTED)
            if invitation.expired_at and invitation.expired_at < timezone.now():
                raise ValidationError(Error.INVITATION_EXPIRED)
            if user.email != invitation.email:
                raise ValidationError(Error.EMAIL_MISMATCH)
            invitation.accepted = True
            invitation.save()

            user.email_verified = True
            user.save()

            if invitation_role == 'tenant':
                assignment = invitation.assigned_object
                if assignment:
                    assignment.status = 'occupied'
                    assignment.save(update_fields=['status'])
        except model.DoesNotExist:
            pass
