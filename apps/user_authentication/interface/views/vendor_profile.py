from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.user_authentication.infrastructure.models import LicenseAndCertificates, Role, Vendor
from apps.user_authentication.interface.serializers import VendorProfileSerializer
from common.constants import Success
from common.utils import CustomResponse

from .property_owner_profile import PropertyOwnerProfileView


class VendorProfileView(PropertyOwnerProfileView):
    """
    API view to create and update a vendor profile.
    """

    serializer = VendorProfileSerializer
    model = Vendor
    role = 'vendor'

    @swagger_auto_schema(request_body=serializer, responses={201: Success.PROFILE_SETUP})
    def post(self, request):
        data = request.data.copy()

        business_license = data.pop('business_license') if request.data.get('business_license') else []
        insurance_certificates = data.pop('insurance_certificates') if request.data.get('insurance_certificates') else []
        other_certificates = data.pop('other_certificates') if request.data.get('other_certificates') else []

        data['user_id'] = request.user.id
        page_saved = data.get('page_saved')

        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()

                for d in business_license:
                    if d:
                        LicenseAndCertificates.objects.create(
                            user_id=request.user, profile_type=self.role, document=d, document_type='business_license'
                        )
                for d in insurance_certificates:
                    if d:
                        LicenseAndCertificates.objects.create(
                            user_id=request.user, profile_type=self.role, document=d, document_type='insurance_certificate'
                        )
                for d in other_certificates:
                    if d:
                        LicenseAndCertificates.objects.create(
                            user_id=request.user, profile_type=self.role, document=d, document_type='other_certificate'
                        )

                Role.objects.create(user_id=request.user, role=self.role)

                if page_saved:
                    user = get_user_model().objects.get(id=request.user.id)
                    user.page_saved = page_saved
                    user.save()

            response_data = serializer.data
            response_data['business_license'] = self.get_certificates(request, 'business_license', self.role)
            response_data['insurance_certificates'] = self.get_certificates(request, 'insurance_certificate', self.role)
            response_data['other_certificates'] = self.get_certificates(request, 'other_certificate', self.role)
            return CustomResponse({'data': response_data, 'message': Success.PROFILE_SETUP}, status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)
