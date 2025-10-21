from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import LicenseAndCertificates, PropertyOwner, Role
from apps.user_management.interface.serializers import LicenseAndCertificatesSerializer, PropertyOwnerProfileSerializer
from common.constants import Success
from common.utils import CustomResponse


class PropertyOwnerProfileView(APIView):
    """
    API view to create and update a user profile.
    """

    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]
    serializer = PropertyOwnerProfileSerializer
    model = PropertyOwner
    role = 'property_owner'

    def get(self, request):
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile)
        roles = list(Role.objects.filter(user_id=request.user).values_list('role', flat=True))
        response_data = {'data': serializer.data}
        response_data['data']['roles'] = roles
        return CustomResponse(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializer,
        responses={
            201: Success.PROFILE_SETUP,
        },
    )
    def post(self, request):
        data = request.data.copy()
        business_license = data.pop('business_license') if request.data.get('business_license') else None

        data['user_id'] = request.user.id
        page_saved = data.get('page_saved')
        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                if business_license:
                    for d in business_license:
                        if d:
                            LicenseAndCertificates.objects.create(
                                user_id=request.user, profile_type=self.role, document=d, document_type='business_license'
                            )

                Role.objects.create(user_id=self.request.user, role=self.role)
                if page_saved:
                    user = get_user_model().objects.get(id=self.request.user.id)
                    user.page_saved = page_saved
                    user.save()

            response_data = serializer.data
            response_data['business_license'] = self.get_certificates(request, 'business_license', self.role)
            return CustomResponse({'data': response_data, 'message': Success.PROFILE_SETUP}, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

    def get_certificates(self, request, type_, profile_type):
        certificates = LicenseAndCertificates.objects.filter(user_id=request.user, document_type=type_, profile_type=profile_type)
        serializer = LicenseAndCertificatesSerializer(certificates, many=True)
        return serializer.data

    def patch(self, request):
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse({'data': serializer.data, 'message': Success.PROFILE_UPDATED}, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)
