from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.user_management.interface.serializers import ResetPasswordSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class ResetPasswordView(APIView):
    """
    API to reset the password.
    """

    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: Success.PASSWORD_UPDATED,
            404: Error.USER_NOT_FOUND,
        },
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
