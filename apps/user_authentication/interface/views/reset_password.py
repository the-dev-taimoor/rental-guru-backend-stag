from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from common.constants import Success, Error
from common.utils import CustomResponse

from apps.user_authentication.interface.serializers import ResetPasswordSerializer



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