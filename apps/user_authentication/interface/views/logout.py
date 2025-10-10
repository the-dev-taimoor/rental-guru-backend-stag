from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from common.constants import Success, Error
from common.utils import CustomResponse

from apps.user_authentication.tokens import CustomAccessToken


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