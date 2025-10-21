from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.user_management.application.services.otp import otp_email
from apps.user_management.interface.serializers import EmailVerifySerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class ForgotPasswordView(APIView):
    """
    API to request forget password.
    """

    @swagger_auto_schema(
        request_body=EmailVerifySerializer,
        responses={
            200: Success.VERIFICATION_CODE_SENT,
            404: Error.USER_NOT_FOUND,
        },
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

            return CustomResponse({'message': Success.VERIFICATION_CODE_SENT}, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)
