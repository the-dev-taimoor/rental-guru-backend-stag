from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import KYCRequest
from apps.user_management.interface.serializers import KYCRequestSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class KYCRequestDetails(APIView):
    """
    API view to get kyc request by super admin.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer = KYCRequestSerializer

    def get(self, request, pk):
        if not request.user.is_superuser:
            return CustomResponse(
                {'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False, 'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC},
                status=status.HTTP_403_FORBIDDEN,
            )

        kyc_request = get_object_or_404(KYCRequest, pk=pk)
        serializer = self.serializer(kyc_request)
        user = kyc_request.user_id
        response_data = {'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email}
        response_data.update(serializer.data)
        return CustomResponse({'data': response_data, 'message': Success.KYC_REQUEST_DETAIL}, status=status.HTTP_200_OK)
