import random
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from apps.properties.infrastructure.models import OwnerInfo
from common.utils import CustomResponse, get_presigned_url, send_email_, unsnake_case
from common.constants import email_templates, Success, Error

from .serializers import (UserSerializer, CustomTokenObtainPairSerializer, EmailVerifySerializer, OTPCreateSerializer,
                          OTPVerifySerializer, OTPEnableSerializer, ResetPasswordSerializer, SelectRoleSerializer,
                          PropertyOwnerProfileSerializer, KYCVerifySerializer, VendorProfileSerializer, KYCRequestSerializer,
                          VendorInvitationSerializer, VendorDetailsByInvitationSerializer, LicenseAndCertificatesSerializer,
                          BulkVendorInviteSerializer, TenantProfileSerializer, TenantInvitationSerializer,
                          InvitationDetailsSerializer, InvitationAgreementSerializer, InvitationAcceptanceSerializer,
                          LeaseManagementSerializer, ResendInvitationSerializer)
from .tokens import CustomAccessToken
from apps.user_authentication.infrastructure.models import (PropertyOwner, Role, KYCRequest, Vendor, ServiceCategory, ServiceSubCategory, VendorInvitation,
                     VendorServices, LicenseAndCertificates, Tenant, TenantInvitation, Agreements)
from apps.properties.infrastructure.models import Property, Unit
from .pagination import KYCRequestsPagination, VendorInvitationPagination, TenantInvitationPagination

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.exceptions import ValidationError, NotFound, NotAuthenticated, APIException
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.db import transaction
from django.conf import settings

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.properties.filters import CustomSearchFilter


import logging

logger = logging.getLogger('django')

def otp_email(user, action, template_variables=None):
    """
    Sends an OTP email to the user using a specified email template.
    Args:
        action: Key to select email template.
        template_variables: Variables for the template.
    """
    try:
        recipient_list = [user.email]
        otp_code = random.randint(1000, 9999)
        if settings.ENV == 'qa':
            otp_code = 1234

        variables = {'USER_FIRST_NAME': user.first_name, 'OTP_CODE': otp_code}
        if template_variables:
            template_variables.update(variables)
        else:
            template_variables = variables

        template = email_templates.get(action)
        subject = template.get('subject')
        duration = int(template.get('duration'))
        html_message = template.get('html_message').format(**template_variables)

        send_mail(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        user.otp = otp_code
        otp_expiry = timezone.now() + timedelta(minutes=duration)
        user.otp_expiry = otp_expiry
        user.save()
    except Exception as e:
        logger.error(str(e))
        raise APIException(Error.RESPONSE_VERIFICATION_EMAIL_ERROR)


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
        except:
            pass
        try:
            tenant_invitations = TenantInvitation.objects.get(email=user.email, accepted=True)
            data_ = InvitationDetailsSerializer(tenant_invitations).data
            data_['role'] = 'tenant'
            invitations.append(data_)
        except:
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
            'property_owner_profile': PropertyOwnerProfileSerializer(
                property_owner_profile).data if property_owner_profile else None,
            'vendor_profile': VendorProfileSerializer(vendor_profile).data if vendor_profile else None,
            'tenant_profile': TenantProfileSerializer(tenant_profile).data if tenant_profile else None,
            'invitations': invitations
            },
            'message': 'User details.'
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

            response_data = {
                "data": user_data,
                "error": None,
                "success": True,
                "message": Success.USER_CREATED
            }
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


class SelectRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer = SelectRoleSerializer
    model = Role

    def post(self, request):
        data = request.data.copy()
        serializer = self.serializer(data=data)
        if Role.objects.filter(user_id=request.user, role=data.get('role')).exists():
            raise ValidationError(Error.ROLE_ALREADY_ASSIGNED.format(data.get('role').replace('_', ' ').title()))
        if serializer.is_valid(raise_exception=True):
            data['user_id'] = request.user
            data['role'] = serializer.validated_data.get('role')
            Role.objects.create(**data)
        return CustomResponse({'message': Success.ROLE_ADDED}, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs) -> Response:
        """
        Create an access and a refresh token for registered user and send an otp before token creation if otp is enabled.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        user = serializer.validated_data
        if user.otp_enable:
            otp_email(user, action='SEND-OTP')
            return CustomResponse({'message': Success.VERIFICATION_CODE_SENT}, status=status.HTTP_200_OK)
        else:
            refresh = RefreshToken.for_user(user)
            response_data = {
                "refresh_token": str(refresh),
                "access_token": str(refresh.access_token)
            }

        return CustomResponse({'data': response_data}, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs) -> Response:
        """
        Handles JWT token refresh request.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return CustomResponse({'data': serializer.validated_data}, status=status.HTTP_200_OK)


class OTPView(APIView):
    @swagger_auto_schema(
        request_body=OTPCreateSerializer,
        responses={
            200: Success.OTP_SENT,
            404: Error.USER_NOT_FOUND,
        },
    )
    def post(self, request):
        """
        Create otp and send email against selected action such as signup, forgot-password etc.
        """
        serializer = OTPCreateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            action = serializer.validated_data['action']

            if not email:
                raise ValidationError({'error': Error.EMAIL_REQUIRED})

            try:
                user = get_user_model().objects.get(email=email, is_active=True)
            except get_user_model().DoesNotExist:
                raise NotFound(Error.USER_NOT_FOUND)

            if action not in ['SIGNUP', 'FORGOT-PASSWORD']:
                if not user.otp_enable:
                    return CustomResponse({'error': Error.OTP_NOT_ENABLED, 'success': False},
                                          status=status.HTTP_400_BAD_REQUEST)

            otp_email(user, action=action)

            return CustomResponse({'message': Success.OTP_SENT}, status=status.HTTP_200_OK)
        return ValidationError(serializer.errors)

    @swagger_auto_schema(
        request_body=OTPEnableSerializer,
        responses={
            200: "Two-Step Verification has been enabled/disabled successfully.",
            404: Error.USER_NOT_FOUND,
        },
    )
    def put(self, request):
        """
        Enables or Disables OTP for a registered user.
        """
        serializer = OTPEnableSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = get_user_model().objects.get(email=email, is_active=True)
            except get_user_model().DoesNotExist:
                raise NotFound(Error.USER_NOT_FOUND)

            user.otp_enable = otp
            user.save()
            message = Success.TWO_STEP_VERIFICATION_ENABLED if otp else Success.TWO_STEP_VERIFICATION_DISABLED

            return CustomResponse({'message': message}, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)


class OTPVerifyView(APIView):
    @swagger_auto_schema(
        request_body=OTPVerifySerializer,
        responses={
            200: Success.OTP_CODE_VALID,
            404: Error.USER_NOT_FOUND,
        },
    )
    def post(self, request):
        """
        Verifies a pre generated OTP and creates tokens for registered user.
        """
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = get_user_model().objects.get(email=email)
            except get_user_model().DoesNotExist:
                raise NotFound(Error.USER_NOT_FOUND)
            if user.otp==otp:
                if user.otp_expiry > timezone.now():
                    refresh = RefreshToken.for_user(user)
                    access_str = str(refresh.access_token)
                    refresh_str = str(refresh)
                    user.email_verified = True
                    user.save()
                    return CustomResponse({'message': Success.OTP_CODE_VALID,
                                           'data': {
                                               'access_token':  access_str,
                                               'refresh_token': refresh_str
                                           }}, status=status.HTTP_200_OK)
                if user.otp_expiry < timezone.now():
                    return CustomResponse({'error': Error.OTP_CODE_EXPIRED, 'message': Error.OTP_CODE_EXPIRED, 'success': False},
                                          status=status.HTTP_400_BAD_REQUEST)
            else:
                return CustomResponse({'error': Error.OTP_CODE_INVALID, 'message': Error.OTP_CODE_INVALID, 'success': False},
                                      status=status.HTTP_400_BAD_REQUEST)
        raise ValidationError(serializer.errors)


class ForgotPasswordView(APIView):
    """
    API to request forget password.
    """

    @swagger_auto_schema(
        request_body=EmailVerifySerializer,
        responses={
            200: Success.VERIFICATION_CODE_SENT,
            404: Error.USER_NOT_FOUND,
        }
    )
    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            if not email:
                raise ValidationError({'error': Error.EMAIL_REQUIRED})

            try:
                user = get_user_model().objects.get(email=email, is_active=True)
            except get_user_model().DoesNotExist:
                raise NotFound(Error.USER_NOT_FOUND)

            otp_email(user, action='FORGOT-PASSWORD')

            return CustomResponse({
                'message': Success.VERIFICATION_CODE_SENT
            }, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)


class ResetPasswordView(APIView):
    """
    API to reset the password.
    """

    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: Success.PASSWORD_UPDATED,
            404: Error.USER_NOT_FOUND,
        }
    )

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise NotFound(Error.USER_NOT_FOUND)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user.password = make_password(new_password)
            user.save()
            return CustomResponse({"message": Success.PASSWORD_UPDATED}, status=status.HTTP_200_OK)

        raise ValidationError(serializer.errors)


class LogoutView(APIView):
    """
    View to log out a user by blacklisting the JWT refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return CustomResponse({'error': Error.REFRESH_TOKEN_REQUIRED, 'success': False,
                                       'message': Error.INVALID_FIELD},
                                      status=status.HTTP_400_BAD_REQUEST)

            ref_token = RefreshToken(refresh_token)
            acc_token = CustomAccessToken(request.auth.token)
            acc_token.blacklist()
            ref_token.blacklist()

            return CustomResponse({'message': Success.LOGGED_OUT}, status=status.HTTP_200_OK)
        except TokenError as e:
            return CustomResponse({
                "data": {},
                "error": str(e),
                "message": Error.TOKEN_ERROR_LOGOUT,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return CustomResponse({'error': e, 'success': False, 'message': Error.ERROR_DURING_LOGOUT},
                                  status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PropertyOwnerProfileView(APIView):
    """
    API view to create and update a user profile.
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]
    serializer = PropertyOwnerProfileSerializer
    model = PropertyOwner
    role = 'property_owner'

    def get(self, request):
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile)
        roles = list(Role.objects.filter(user_id=request.user).values_list('role', flat=True))
        response_data = {'data': serializer.data}
        response_data['data']['roles'] = roles
        return CustomResponse(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializer,
        responses={
            201: Success.PROFILE_SETUP,
        }
    )
    def post(self, request):
        data = request.data.copy()
        business_license = data.pop('business_license') if request.data.get('business_license') else None

        data['user_id'] = request.user.id
        page_saved = data.get('page_saved')
        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():

                serializer.save()
                if business_license:
                    for d in business_license:
                        if d:
                            LicenseAndCertificates.objects.create(user_id=request.user, profile_type=self.role, document=d, document_type='business_license')

                Role.objects.create(user_id=self.request.user, role=self.role)
                if page_saved:
                    user = get_user_model().objects.get(id=self.request.user.id)
                    user.page_saved = page_saved
                    user.save()

            response_data = serializer.data
            response_data['business_license'] = self.get_certificates(request, 'business_license', self.role)
            return CustomResponse({'data': response_data, 'message': Success.PROFILE_SETUP},
                                  status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

    def get_certificates(self, request, type_, profile_type):
        certificates = LicenseAndCertificates.objects.filter(user_id=request.user, document_type=type_, profile_type=profile_type)
        serializer = LicenseAndCertificatesSerializer(certificates, many=True)
        return serializer.data

    def patch(self, request):
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse({'data': serializer.data, 'message': Success.PROFILE_UPDATED},
                                  status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)


class KYCRequests(APIView):
    """
    API view to create kyc request.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer = KYCVerifySerializer

    @swagger_auto_schema(
        operation_description="Submit KYC details including the ID type and images.",
        request_body=serializer,
        responses={
            201: "Your documents have been submitted.",
            400: "Bad Request if the fields are missing or invalid.",
        },
        manual_parameters=[
            openapi.Parameter(
                'id_type', openapi.IN_FORM, description="ID type (e.g., CNIC, Passport, Driving license.)",
                type=openapi.TYPE_STRING, required=True),
            openapi.Parameter(
                'front_image', openapi.IN_FORM, description="Front image of the ID", type=openapi.TYPE_FILE,
                required=True),
            openapi.Parameter(
                'back_image', openapi.IN_FORM, description="Back image of the ID", type=openapi.TYPE_FILE,
                required=True),
            openapi.Parameter(
                'notes', openapi.IN_FORM, description="Additional notes for the KYC", type=openapi.TYPE_STRING,
                required=False),
        ]
    )
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user_id'] = request.user.id
        serializer = self.serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return CustomResponse({
                'message': Success.DOCUMENTS_SUBMITTED
            }, status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)


class KYCRequestDetails(APIView):
    """
    API view to get kyc request by super admin.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer = KYCRequestSerializer

    def get(self, request, pk):
        if not request.user.is_superuser:
            return CustomResponse({'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False,
                                   'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC}, status=status.HTTP_403_FORBIDDEN)

        kyc_request = get_object_or_404(KYCRequest, pk=pk)
        serializer = self.serializer(kyc_request)
        user = kyc_request.user_id
        response_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
        response_data.update(serializer.data)
        return CustomResponse({'data': response_data, 'message': Success.KYC_REQUEST_DETAIL},
                              status=status.HTTP_200_OK)


class KYCView(APIView):
    """
    API view to view kyc requests by Super Admin only.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KYCVerifySerializer
    pagination_class = KYCRequestsPagination

    @swagger_auto_schema(
        operation_description="Get all KYC requests with search and filter functionality. "
                              "Use search to filter with name and status to filter on the basis of status column in query params.",
        responses={
            200: "List of KYC requests with pagination, search, and filter options.",
            403: "Permission denied. Only super admins can access this endpoint.",
        }
    )
    def get(self, request, *args, **kwargs):
        basename = request.resolver_match.url_name

        if basename == 'kyc_stats':
            return self.get_stats(request)
        else:
            return self.get_list(request)

    def get_list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return CustomResponse({'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False,
                                   'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC}, status=status.HTTP_403_FORBIDDEN)

        search_query = request.query_params.get('search', None)
        status_filter = request.query_params.get('status', None)

        kyc_requests = KYCRequest.objects.all().select_related('user_id').order_by('-id')

        if search_query:
            kyc_requests = kyc_requests.filter(
                Q(user_id__first_name__icontains=search_query) |
                Q(user_id__last_name__icontains=search_query) |
                Q(user_id__email__icontains=search_query)
            )

        if status_filter:
            kyc_requests = kyc_requests.filter(status=status_filter)

        user_ids = kyc_requests.values_list('user_id', flat=True).distinct()

        roles = Role.objects.filter(user_id__in=user_ids).values('user_id', 'role')
        user_roles = {role['user_id']: role['role'] for role in roles}

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(kyc_requests, request)

        response_data = []
        for kyc in result_page:
            kyc_data = KYCVerifySerializer(kyc).data
            user_role = user_roles.get(kyc.user_id.id, 'Not assigned')
            user_data = {
                'kyc_id': kyc.id,
                'full_name': f'{kyc.user_id.first_name} {kyc.user_id.last_name}',
                'email': kyc.user_id.email,
                'status': kyc.status,
                'role': user_role,
                'registration_date': kyc.created_at.strftime('%Y-%m-%d'),
                'front_image': get_presigned_url(kyc.front_image.name),
                'back_image': get_presigned_url(kyc.back_image.name) if kyc.back_image else None,
            }
            kyc_data.update(user_data)
            response_data.append(kyc_data)

        return paginator.get_paginated_response(response_data)

    def get_stats(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return CustomResponse({'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False,
                                   'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC}, status=status.HTTP_403_FORBIDDEN)
        counts = KYCRequest.objects.aggregate(
            total_requests=Count('id'),
            total_pending=Count('id', filter=Q(status='pending')),
            total_approved=Count('id', filter=Q(status='approved')),
            total_rejected=Count('id', filter=Q(status='rejected')),
        )
        return CustomResponse({'data': counts, 'message': Success.KYC_STATS}, status=status.HTTP_200_OK)

    def send_kyc_response(self, user, kyc_request):
        subject = 'Rental Guru – KYC Feedback'
        html_message = f"""
                        <html>
                        <body>
                            <p>Hi {user.first_name},</p>
                            <p>This email is in response of your KYC request.</p>
                            <p>Your request is {kyc_request.status}.</p>
                            <p>Reason: {kyc_request.review_notes if kyc_request.review_notes else ''}</p>
                        </body>
                        </html>
                        """
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        try:
            send_mail(
                subject,
                '',
                from_email,
                recipient_list,
                fail_silently=False,
                html_message=html_message,
            )
        except Exception as e:
            return CustomResponse({
                'error': e,
                'success': False,
                'message': Error.KYC_RESPONSE_EMAIL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        if not request.user.is_superuser:
            return CustomResponse({'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False,
                                   'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC},
                                  status=status.HTTP_403_FORBIDDEN)

        kyc_id = request.data.get('kyc_id')
        kyc_status = request.data.get('status')
        review_notes = request.data.get('review_notes')
        try:
            kyc_request = KYCRequest.objects.get(id=kyc_id)
        except KYCRequest.DoesNotExist:
            raise NotFound('KYC not found.')

        if kyc_status:
            if kyc_status not in ['approved', 'rejected']:
                return CustomResponse({'error': Error.KYC_STATUS_INVALID, 'success': False,
                                       'message': Error.KYC_STATUS_INVALID},
                                      status=status.HTTP_400_BAD_REQUEST)

            kyc_request.status = kyc_status
            kyc_request.reviewed_at = timezone.now()
        if review_notes:
            kyc_request.review_notes = review_notes
        kyc_request.save()

        self.send_kyc_response(kyc_request.user_id, kyc_request)
        return CustomResponse({'message': Success.KYC_REQUEST_UPDATED_EMAIL_SENT}, status=status.HTTP_200_OK)


class VendorProfileView(PropertyOwnerProfileView):
    """
    API view to create and update a vendor profile.
    """
    serializer = VendorProfileSerializer
    model = Vendor
    role = 'vendor'

    @swagger_auto_schema(
        request_body=serializer,
        responses={201: Success.PROFILE_SETUP}
    )
    def post(self, request):
        data = request.data.copy()

        business_license = data.pop('business_license') if request.data.get('business_license') else []
        insurance_certificates = data.pop('insurance_certificates') if request.data.get('insurance_certificates') else []
        other_certificates = data.pop('other_certificates') if request.data.get('other_certificates') else []

        data['user_id'] = request.user.id
        page_saved = data.get('page_saved')

        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                profile_instance = serializer.save()

                for d in business_license:
                    if d:
                        LicenseAndCertificates.objects.create(user_id=request.user, profile_type=self.role, document=d, document_type='business_license')
                for d in insurance_certificates:
                    if d:
                        LicenseAndCertificates.objects.create(user_id=request.user, profile_type=self.role, document=d, document_type='insurance_certificate')
                for d in other_certificates:
                    if d:
                        LicenseAndCertificates.objects.create(user_id=request.user, profile_type=self.role, document=d, document_type='other_certificate')

                Role.objects.create(user_id=request.user, role=self.role)

                if page_saved:
                    user = get_user_model().objects.get(id=request.user.id)
                    user.page_saved = page_saved
                    user.save()

            response_data = serializer.data
            response_data['business_license'] = self.get_certificates(request, 'business_license', self.role)
            response_data['insurance_certificates'] = self.get_certificates(request, 'insurance_certificate', self.role)
            response_data['other_certificates'] = self.get_certificates(request, 'other_certificate', self.role)
            return CustomResponse(
                {'data': response_data, 'message': Success.PROFILE_SETUP},
                status=status.HTTP_201_CREATED
            )

        raise ValidationError(serializer.errors)


class ServiceCategoriesView(ModelViewSet):
    """
    To get the list of pre-saved categories for vendor offered services.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceCategory.objects.all()

    def list(self, request, *args, **kwargs):
        subcategories_qs = ServiceSubCategory.objects.all()
        categories = self.queryset.prefetch_related(
            Prefetch('category', queryset=subcategories_qs, to_attr='subcategories_list')
        )

        categories_list = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'subcategories': [{'id': sub.id, 'name': sub.name} for sub in category.subcategories_list]
            }
            categories_list.append(category_data)

        return CustomResponse({'data': categories_list, 'message': Success.SERVICE_CATEGORIES},
                              status=status.HTTP_200_OK)


class ServiceSubCategoriesView(ModelViewSet):
    """
    To get the list of pre-saved sub-categories for vendor offered services.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceSubCategory.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category_id']

    def list(self, request, *args, **kwargs):
        subcategories = self.filter_queryset(self.queryset.values('id', 'name'))
        result = list(subcategories)

        return CustomResponse({'data': result, 'message': Success.SERVICE_SUBCATEGORIES}, status=status.HTTP_200_OK)


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


class VendorRolesView(APIView):
    """
    API view to get available vendor roles.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        roles = []
        for role_value, role_display in VendorInvitation.VENDOR_ROLE_CHOICES:
            roles.append({'value': role_value, 'label': role_display})

        return CustomResponse({"message": Success.VENDOR_ROLES_LIST, "data": roles}, status=status.HTTP_200_OK)


class VendorDetailsByInvitationView(APIView):
    """
    API view to get vendor details by invitation ID.
    Returns vendor information organized in different tabs/sections.

    URL: GET /v1/api/user-authentication/invited-vendor-details/{invitation_id}/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invitation_id):
        """
        Get vendor details using invitation ID.

        Returns:
        - invitation_info: Basic invitation details
        - basic_info: Vendor basic information (name, contact, experience, etc.)
        - business_info: Business information (company details, registration, etc.)
        - services_info: Services offered and service area
        - certification_info: Insurance and certificates
        - jobs_info: Job statistics (earnings, completed jobs, ratings)
        - payments_info: Payment information
        """
        try:
            invitation = VendorInvitation.objects.get(id=invitation_id, sender=request.user)
        except VendorInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invitation.accepted:
            return CustomResponse(
                {"error": Error.VENDOR_INVITATION_NOT_ACCEPTED},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = get_user_model().objects.get(email=invitation.email)
        except get_user_model().DoesNotExist:
            return CustomResponse(
                {"error": Error.VENDOR_NOT_FOUND_FOR_INVITATION},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            vendor = Vendor.objects.get(user_id=user)
        except Vendor.DoesNotExist:
            return CustomResponse(
                {"error": Error.VENDOR_NOT_FOUND_FOR_INVITATION},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            'basic_info': self._get_basic_info(vendor, user),
            'vendor_info': self._get_vendor_info(vendor, user),
            'services': self._get_services_info(vendor),
            'certification_info': self._get_certification_info(vendor)
        }

        return CustomResponse(
            {
                "message": Success.VENDOR_DETAILS_RETRIEVED,
                "data": response_data
            },
            status=status.HTTP_200_OK
        )

    def _get_basic_info(self, vendor, user):
        return {
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'vendor_role': vendor.vendor_role,
            'phone_number': user.phone_number or "Not provided",
            'email': user.email,
            'description': vendor.description
        }

    def _get_vendor_info(self, vendor, user):
        def to_12h_pm(hh):
            dt = datetime.strptime(str(hh), "%H:%M")
            label = dt.strftime("%I%p").lstrip("0")
            return label

        parts = []
        if vendor.availability:
            for day, times in vendor.daily_availability.items():
                start = to_12h_pm(times["from"])
                end = to_12h_pm(times["to"])
                parts.append(f"{day} {start}-{end}")
        else:
            parts.append("Not Available")

        return {
            'years_of_experience': f"{vendor.years_of_experience} years" if vendor.years_of_experience else "Not specified",
            'availability': ", ".join(parts),
            'emergency_services': vendor.emergency_services,
            'languages': vendor.languages or "Not specified",
            'insurance_coverage': vendor.insurance_coverage,
            'registration_type': vendor.registration_type,
            'business_name': vendor.business_name or "Not provided",
            'business_website': vendor.business_website or "Not provided",
            'business_address': vendor.business_address or "Not provided",
            'business_type': vendor.business_type or "Not specified",
            'registration_id': vendor.company_registration_number or "Not provided",
            'business_license': self._get_business_license_url(vendor)
        }

    def _get_business_license_url(self, vendor):
        data = []
        licenses = LicenseAndCertificates.objects.filter(user_id=vendor.user_id, profile_type='vendor', document_type='business_license')
        for license in licenses:
            cert_data = {
                'name': unsnake_case(license.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(license.document.name)
            }
            data.append(cert_data)
        return data

    def _get_services_info(self, vendor):
        """Get services information"""
        # Get vendor services
        vendor_services = VendorServices.objects.filter(user_id=vendor.user_id) \
            .select_related('category_id', 'subcategory_id')

        services_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            services_dict[category_name].append(subcategory_name)

        return dict(services_dict)

    def _get_certification_info(self, vendor):
        """Get certification information"""
        data = []
        certificates = LicenseAndCertificates.objects.filter(user_id=vendor.user_id, profile_type='vendor', document_type='insurance_certificate')
        for certificate in certificates:
            cert_data = {
                'name': unsnake_case(certificate.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(certificate.document.name)
            }
            data.append(cert_data)

        certificates = LicenseAndCertificates.objects.filter(user_id=vendor.user_id, profile_type='vendor', document_type='other_certificate')
        for certificate in certificates:
            cert_data = {
                'name': unsnake_case(certificate.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(certificate.document.name)
            }
            data.append(cert_data)
        return data


class BulkVendorInviteAPIView(APIView):
    parser_classes = [MultiPartParser]
    serializer_class = BulkVendorInviteSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        vendors_invited = list()
        all_errors = list()
        all_vendors = serializer.validated_data
        for vendor in all_vendors:
            email = vendor.get('email')
            role = vendor.get('role')
            first_name = vendor.get('first_name')
            last_name = vendor.get('last_name')

            if not serializer.is_valid():
                all_errors.append(serializer.errors)
                continue

            if Vendor.objects.filter(user_id__email=email).exists():
                all_errors.append(Error.VENDOR_ALREADY_EXISTS_V2.format(email))
                continue

            if VendorInvitation.objects.filter(email=email, sender=request.user, role=role).exists():
                if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, accepted=True).exists():
                    all_errors.append(Error.VENDOR_INVITATION_ALREADY_ACCEPTED.format(email, role))
                    continue
                if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__gte=timezone.now()).exists():
                    all_errors.append(Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role))
                    continue
                if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False).exists():
                    VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False).delete()

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

                vendors_invited.append(email)

            except Exception as e:
                # Handle IntegrityError for duplicate invitations
                if 'UNIQUE constraint failed' in str(e) or 'duplicate key value' in str(e):
                    role_display = dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(role, role)
                    return all_errors.append(Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role_display))
                all_errors.append(Error.VENDOR_INVITATION_SEND_FAILED.format(str(e)))
        data_ = Error.INVITATION_SENT_TO_EMAIL.format(', '.join(vendors_invited)) if vendors_invited else {}
        return CustomResponse(
            {
                "message": Success.VENDOR_INVITATION_SENT,
                "data": data_,
                "error": all_errors
            },
            status=status.HTTP_201_CREATED
        )


class TenantProfileView(PropertyOwnerProfileView):
    """
        API view to create and update a tenant profile.
        """
    serializer = TenantProfileSerializer
    model = Tenant
    role = 'tenant'

    @swagger_auto_schema(
        request_body=serializer,
        responses={201: Success.PROFILE_SETUP}
    )
    def post(self, request):
        data = request.data.copy()
        data['user_id'] = request.user.id

        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                Role.objects.create(user_id=request.user, role=self.role)
            return CustomResponse(
                {'data': serializer.data, 'message': Success.PROFILE_SETUP},
                status=status.HTTP_201_CREATED
            )

        raise ValidationError(serializer.errors)

    def patch(self, request):
        """
        Update tenant profile.
        """
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse({'data': serializer.data, 'message': Success.PROFILE_UPDATED},
                                  status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)


class TenantInvitationView(APIView):
    """
    API view to send tenant invitations.
    Accepts first_name, last_name, email, assignment_type, assignment_id, tenant_type, lease details in the payload.
    Supports search functionality for tenant name, email, and tenant_type.
    """
    queryset = TenantInvitation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TenantInvitationSerializer
    filter_backends = [DjangoFilterBackend, CustomSearchFilter, OrderingFilter]
    filterset_fields = ['tenant_type', 'accepted', 'blocked', 'assignment_type', 'assignment_id']
    search_fields = ['first_name', 'last_name', 'email', 'tenant_type']
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
        Send tenant invitation email and save invitation record.

        Expected payload:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "assignment_type": "unit",  # or "property"
            "assignment_id": 1,
            "tenant_type": "individual",
            "lease_amount": 2000,
            "security_deposit": 4000,
            "lease_start_date": "2025-02-01",
            "lease_end_date": "2026-02-01",
            "lease_agreement": <file>
        }
        """
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email')
        tenant_type = request.data.get('tenant_type')
        assignment_type = request.data.get('assignment_type')
        assignment_id = request.data.get('assignment_id')
        tenant_type_display = dict(TenantInvitation.TENANT_TYPE_CHOICES).get(tenant_type, tenant_type)

        # Check if tenant already exists
        if Tenant.objects.filter(user_id__email=email).exists():
            return CustomResponse({"error": Error.TENANT_ALREADY_EXISTS}, status=status.HTTP_400_BAD_REQUEST)

        # Validate assignment exists and belongs to user
        if assignment_type == 'property':
            try:
                assigned_obj = Property.objects.get(id=assignment_id, property_owner=request.user)
                assignment_name = assigned_obj.name
                if assigned_obj.status == 'occupied':
                    return CustomResponse({"error": Error.PROPERTY_OCCUPIED}, status=status.HTTP_400_BAD_REQUEST)
            except Property.DoesNotExist:
                return CustomResponse({"error": Error.PROPERTY_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        elif assignment_type == 'unit':
            try:
                assigned_obj = Unit.objects.get(id=assignment_id, property__property_owner=request.user)
                assignment_name = f"{assigned_obj.number} - {assigned_obj.property.name}"
                if assigned_obj.status == 'occupied':
                    return CustomResponse({"error": Error.UNIT_OCCUPIED}, status=status.HTTP_400_BAD_REQUEST)
            except Unit.DoesNotExist:
                return CustomResponse({"error": Error.UNIT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        else:
            return CustomResponse({"error": "assignment_type must be either 'unit' or 'property'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing invitations and clean up expired ones
        existing_invitation = TenantInvitation.objects.filter(
            email=email, sender=request.user, tenant_type=tenant_type,
            assignment_type=assignment_type, assignment_id=assignment_id
        ).first()

        if existing_invitation:
            if existing_invitation.expired_at <= timezone.now() and not existing_invitation.accepted:
                # Delete expired invitation
                existing_invitation.delete()
            elif existing_invitation.accepted:
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_ALREADY_ACCEPTED.format(email, tenant_type_display, assignment_name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Clean up expired invitations for same email+tenant_type+sender+assignment
                TenantInvitation.objects.filter(
                    email=email,
                    sender=request.user,
                    tenant_type=tenant_type,
                    assignment_type=assignment_type,
                    assignment_id=assignment_id,
                    expired_at__lte=timezone.now(),
                    accepted=False
                ).delete()

        if not serializer.is_valid():
            if 'must make a unique set' in str(serializer.errors):
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_ALREADY_SENT.format(email, tenant_type_display, assignment_name)},
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
        tenant_type = validated_data['tenant_type']
        assignment_type = validated_data['assignment_type']
        assignment_id = validated_data['assignment_id']
        lease_amount = validated_data['lease_amount']
        security_deposit = validated_data.get('security_deposit', 0)
        lease_start_date = validated_data['lease_start_date']
        lease_end_date = validated_data['lease_end_date']
        lease_agreement = validated_data.get('lease_agreement')

        try:
            # Get owner name for email
            owner_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if not owner_name:
                owner_name = request.user.email

            with transaction.atomic():
                invitation = TenantInvitation.objects.create(
                    sender=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    assignment_type=assignment_type,
                    assignment_id=assignment_id,
                    tenant_type=tenant_type,
                    lease_amount=lease_amount,
                    security_deposit=security_deposit,
                    lease_start_date=lease_start_date,
                    lease_end_date=lease_end_date,
                    expired_at=timezone.now() + timedelta(days=5)
                )

                agreement = Agreements.objects.create(
                    invitation=invitation,
                    lease_agreement=lease_agreement
                )

            email_variables = {
                'TENANT_FIRST_NAME': first_name,
                'OWNER_NAME': owner_name,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?tenant=true&invitation_id={invitation.id}"
            }

            send_email_(email, email_variables, 'INVITE-TENANT')

            response_data = {
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'tenant_type': invitation.tenant_type,
                'assignment_type': invitation.assignment_type,
                'assignment_id': invitation.assignment_id,
                'assignment_name': assignment_name,
                'lease_amount': invitation.lease_amount,
                'security_deposit': invitation.security_deposit,
                'lease_agreement_url': get_presigned_url(agreement.lease_agreement.name) if agreement.lease_agreement else None,
                'lease_start_date': invitation.lease_start_date,
                'lease_end_date': invitation.lease_end_date,
                'lease_ended': True if invitation.lease_end_date <= timezone.now().date() else False,
                'created_at': invitation.created_at
            }

            return CustomResponse(
                {
                    "message": Success.TENANT_INVITATION_SENT,
                    "data": response_data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return CustomResponse(
                {"error": Error.TENANT_INVITATION_SEND_FAILED.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Get list of tenant invitations with pagination and filtering"""
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        paginator = TenantInvitationPagination()
        result_page = paginator.paginate_queryset(filtered_queryset, request)

        invitation_data = []
        for invitation in result_page:
            # Get assignment name based on type
            assigned_obj = invitation.assigned_object
            assignment_name = ""
            if assigned_obj:
                if invitation.assignment_type == 'property':
                    assignment_name = assigned_obj.name
                elif invitation.assignment_type == 'unit':
                    assignment_name = f"{assigned_obj.number} - {assigned_obj.property.name}"

            invitation_data.append({
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'tenant_type': invitation.tenant_type,
                'tenant_type_display': dict(TenantInvitation.TENANT_TYPE_CHOICES).get(invitation.tenant_type, invitation.tenant_type),
                'assignment_type': invitation.assignment_type,
                'assignment_id': invitation.assignment_id,
                'assignment_name': assignment_name,
                'lease_amount': invitation.lease_amount,
                'security_deposit': invitation.security_deposit,
                'lease_start_date': invitation.lease_start_date,
                'lease_end_date': invitation.lease_end_date,
                'lease_ended': True if invitation.lease_end_date <= timezone.now().date() else False,
                'accepted': invitation.accepted,
                'blocked': invitation.blocked,
                'created_at': invitation.created_at
            })

        return paginator.get_paginated_response(invitation_data)

    def put(self, request):
        """
        Update invitation agreement status and signed agreement file.
        Expected payload:
        - invitation_id (integer): The invitation ID to update
        - agreed (boolean): Must be true to update agreement
        - signed_agreement (file): The signed agreement file
        """
        serializer = InvitationAgreementSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        agreed = validated_data.get('agreed')
        invitation_id = validated_data.get('invitation_id')
        signed_agreement = validated_data.get('signed_agreement')

        try:
            invitation = TenantInvitation.objects.get(id=invitation_id)
        except TenantInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            agreement = Agreements.objects.get(invitation=invitation_id)
        except Agreements.DoesNotExist:
            return CustomResponse(
                {"error": Error.AGREEMENT_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse(
                {"error": Error.INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            invitation.agreed = agreed
            agreement.signed_agreement = signed_agreement
            invitation.save(update_fields=['agreed', 'updated_at'])
            agreement.save(update_fields=['signed_agreement'])
        return CustomResponse({"message": Success.INVITATION_AGREEMENT_UPDATED}, status=status.HTTP_200_OK)


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
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation_id = serializer.validated_data['invitation_id']
        action = serializer.validated_data['action']

        try:
            invitation = TenantInvitation.objects.get(id=invitation_id, sender=request.user)
        except TenantInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.TENANT_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

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

                return CustomResponse(
                    {"message": Success.LEASE_ENDED_SUCCESSFULLY},
                    status=status.HTTP_200_OK
                )

            elif action == 'renew':
                # Renew lease scenario
                # Update the lease end date
                with transaction.atomic():
                    invitation.lease_end_date = serializer.validated_data.get('lease_end_date')
                    invitation.lease_amount = serializer.validated_data['rent_amount']
                    invitation.security_deposit = serializer.validated_data.get('security_deposit', invitation.security_deposit)
                    invitation.lease_start_date = serializer.validated_data['lease_start_date']
                    invitation.agreed = False
                    invitation.save(update_fields=['lease_start_date', 'lease_end_date', 'lease_amount',
                                                   'security_deposit', 'agreed', 'updated_at'])
                    Agreements.objects.create(
                        invitation=invitation,
                        lease_agreement=serializer.validated_data['lease_agreement']
                    )

                return CustomResponse(
                    {"message": Success.LEASE_RENEWED_SUCCESSFULLY},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            error_message = Error.LEASE_END_FAILED if action == 'end' else Error.LEASE_RENEWAL_FAILED
            return CustomResponse(
                {"error": error_message.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


class TenantTypesView(APIView):
    """
    API view to get all available tenant types.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get list of all tenant types"""
        tenant_types = []
        for tenant_type_value, tenant_type_display in TenantInvitation.TENANT_TYPE_CHOICES:
            tenant_types.append({'value': tenant_type_value, 'label': tenant_type_display})

        return CustomResponse({"message": "Tenant types retrieved successfully.", "data": tenant_types}, status=status.HTTP_200_OK)


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
            return CustomResponse(
                {"error": Error.INVALID_INVITATION_TYPE},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation = None

        # Try to fetch vendor invitation if vendor=true
        if vendor:
            try:
                invitation = VendorInvitation.objects.get(id=invitation_id)
            except VendorInvitation.DoesNotExist:
                if not tenant:  # If only vendor was requested and not found
                    return CustomResponse(
                        {"error": Error.INVITATION_NOT_FOUND},
                        status=status.HTTP_404_NOT_FOUND
                    )

        # Try to fetch tenant invitation if tenant=true and vendor invitation not found
        if tenant and invitation is None:
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse(
                    {"error": Error.INVITATION_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )

        if invitation is None:
            return CustomResponse(
                {"error": Error.INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse(
                {"error": Error.INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvitationDetailsSerializer(invitation)

        return CustomResponse(
            {
                "message": Success.INVITATION_DETAILS_RETRIEVED,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

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
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

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
                return CustomResponse(
                    {"error": Error.VENDOR_INVITATION_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif tenant:
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse(
                {"error": Error.INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invitation.accepted and accept:
            return CustomResponse(
                {"error": Error.INVITATION_ALREADY_ACCEPTED},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        return CustomResponse(
            {"message": message},
            status=status.HTTP_200_OK
        )


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
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        invitation_id = validated_data['invitation_id']
        role = validated_data.get('role', 'vendor')

        invitation = None
        if role=='vendor':
            try:
                invitation = VendorInvitation.objects.get(id=invitation_id)
            except VendorInvitation.DoesNotExist:
                return CustomResponse(
                    {"error": Error.VENDOR_INVITATION_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif role=='tenant':
            try:
                invitation = TenantInvitation.objects.get(id=invitation_id)
            except TenantInvitation.DoesNotExist:
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )

        if invitation.accepted:
            return CustomResponse(
                {"error": Error.INVITATION_ALREADY_ACCEPTED},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Resend invitation email
        if role=='vendor':
            variables = {
                'VENDOR_FIRST_NAME': invitation.first_name,
                'VENDOR_LAST_NAME': invitation.last_name,
                'VENDOR_ROLE': invitation.role,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?vendor=true&invitation_id={invitation.id}"
            }
            send_email_(invitation.email, variables, 'INVITE-VENDOR')
        elif role=='tenant':
            variables = {
                'TENANT_FIRST_NAME': invitation.first_name,
                'OWNER_NAME': invitation.sender.first_name,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?tenant=true&invitation_id={invitation.id}"
            }
            send_email_(invitation.email, variables, 'INVITE-TENANT')

        invitation.expired_at = timezone.now() + timedelta(days=5)
        invitation.save(update_fields=['expired_at'])

        return CustomResponse(
            {"message": Success.INVITATION_RESENT},
            status=status.HTTP_200_OK
        )