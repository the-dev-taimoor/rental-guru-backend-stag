from rest_framework import status
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from common.utils import CustomResponse


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