from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.user_management.application.services.otp import otp_email
from apps.user_management.interface.serializers import OTPCreateSerializer, OTPEnableSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


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
                    return CustomResponse({'error': Error.OTP_NOT_ENABLED, 'success': False}, status=status.HTTP_400_BAD_REQUEST)

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
