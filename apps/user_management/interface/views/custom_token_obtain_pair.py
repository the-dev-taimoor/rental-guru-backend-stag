from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user_management.application.services.otp import otp_email
from apps.user_management.interface.serializers import CustomTokenObtainPairSerializer
from common.constants import Success
from common.utils import CustomResponse


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
            response_data = {"refresh_token": str(refresh), "access_token": str(refresh.access_token)}

        return CustomResponse({'data': response_data}, status=status.HTTP_200_OK)
