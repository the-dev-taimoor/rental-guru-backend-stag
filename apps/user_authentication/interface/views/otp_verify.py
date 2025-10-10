from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from django.utils import timezone

from common.constants import Success, Error
from common.utils import CustomResponse

from apps.user_authentication.interface.serializers import OTPVerifySerializer


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