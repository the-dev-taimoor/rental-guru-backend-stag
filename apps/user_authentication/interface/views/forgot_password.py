from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model

from common.constants import Success, Error
from common.utils import CustomResponse

from apps.user_authentication.interface.serializers import EmailVerifySerializer
from apps.user_authentication.application.services.otp import otp_email


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