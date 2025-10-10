from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from common.constants import Success
from common.utils import CustomResponse

from apps.user_authentication.interface.serializers import KYCVerifySerializer


class KYCRequests(APIView):
    """
    API view to create kyc request.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer = KYCVerifySerializer

    @swagger_auto_schema(
        operation_description="Submit KYC details including the ID type and images.",
        request_body=serializer,
        responses={
            201: "Your documents have been submitted.",
            400: "Bad Request if the fields are missing or invalid.",
        },
        manual_parameters=[
            openapi.Parameter(
                'id_type', openapi.IN_FORM, description="ID type (e.g., CNIC, Passport, Driving license.)",
                type=openapi.TYPE_STRING, required=True),
            openapi.Parameter(
                'front_image', openapi.IN_FORM, description="Front image of the ID", type=openapi.TYPE_FILE,
                required=True),
            openapi.Parameter(
                'back_image', openapi.IN_FORM, description="Back image of the ID", type=openapi.TYPE_FILE,
                required=True),
            openapi.Parameter(
                'notes', openapi.IN_FORM, description="Additional notes for the KYC", type=openapi.TYPE_STRING,
                required=False),
        ]
    )
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user_id'] = request.user.id
        serializer = self.serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return CustomResponse({
                'message': Success.DOCUMENTS_SUBMITTED
            }, status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)
