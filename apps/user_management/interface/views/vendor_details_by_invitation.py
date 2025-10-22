from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import LicenseAndCertificate, Vendor, VendorInvitation, VendorService
from apps.user_management.interface.serializers import BulkVendorInviteSerializer
from common.constants import Error, Success
from common.utils import CustomResponse, get_presigned_url, send_email_, unsnake_case


class VendorDetailsByInvitationView(APIView):
    """
    API view to get vendor details by invitation ID.
    Returns vendor information organized in different tabs/sections.

    URL: GET /v1/api/user-authentication/invited-vendor-details/{invitation_id}/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invitation_id):
        """
        Get vendor details using invitation ID.

        Returns:
        - invitation_info: Basic invitation details
        - basic_info: Vendor basic information (name, contact, experience, etc.)
        - business_info: Business information (company details, registration, etc.)
        - services_info: Services offered and service area
        - certification_info: Insurance and certificates
        - jobs_info: Job statistics (earnings, completed jobs, ratings)
        - payments_info: Payment information
        """
        try:
            invitation = VendorInvitation.objects.get(id=invitation_id, sender=request.user)
        except VendorInvitation.DoesNotExist:
            return CustomResponse({"error": Error.VENDOR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if not invitation.accepted:
            return CustomResponse({"error": Error.VENDOR_INVITATION_NOT_ACCEPTED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_user_model().objects.get(email=invitation.email)
        except get_user_model().DoesNotExist:
            return CustomResponse({"error": Error.VENDOR_NOT_FOUND_FOR_INVITATION}, status=status.HTTP_404_NOT_FOUND)

        try:
            vendor = Vendor.objects.get(user_id=user)
        except Vendor.DoesNotExist:
            return CustomResponse({"error": Error.VENDOR_NOT_FOUND_FOR_INVITATION}, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            'basic_info': self._get_basic_info(vendor, user),
            'vendor_info': self._get_vendor_info(vendor, user),
            'services': self._get_services_info(vendor),
            'certification_info': self._get_certification_info(vendor),
        }

        return CustomResponse({"message": Success.VENDOR_DETAILS_RETRIEVED, "data": response_data}, status=status.HTTP_200_OK)

    def _get_basic_info(self, vendor, user):
        return {
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'vendor_role': vendor.vendor_role,
            'phone_number': user.phone_number or "Not provided",
            'email': user.email,
            'description': vendor.description,
        }

    def _get_vendor_info(self, vendor, user):
        def to_12h_pm(hh):
            dt = datetime.strptime(str(hh), "%H:%M")
            label = dt.strftime("%I%p").lstrip("0")
            return label

        parts = []
        if vendor.availability:
            for day, times in vendor.daily_availability.items():
                start = to_12h_pm(times["from"])
                end = to_12h_pm(times["to"])
                parts.append(f"{day} {start}-{end}")
        else:
            parts.append("Not Available")

        return {
            'years_of_experience': f"{vendor.years_of_experience} years" if vendor.years_of_experience else "Not specified",
            'availability': ", ".join(parts),
            'emergency_services': vendor.emergency_services,
            'languages': vendor.languages or "Not specified",
            'insurance_coverage': vendor.insurance_coverage,
            'registration_type': vendor.registration_type,
            'business_name': vendor.business_name or "Not provided",
            'business_website': vendor.business_website or "Not provided",
            'business_address': vendor.business_address or "Not provided",
            'business_type': vendor.business_type or "Not specified",
            'registration_id': vendor.company_registration_number or "Not provided",
            'business_license': self._get_business_license_url(vendor),
        }

    def _get_business_license_url(self, vendor):
        data = []
        licenses = LicenseAndCertificate.objects.filter(user_id=vendor.user_id, profile_type='vendor', document_type='business_license')
        for license in licenses:
            cert_data = {
                'name': unsnake_case(license.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(license.document.name),
            }
            data.append(cert_data)
        return data

    def _get_services_info(self, vendor):
        """Get services information"""
        # Get vendor services
        vendor_services = VendorService.objects.filter(user_id=vendor.user_id).select_related('category_id', 'subcategory_id')

        services_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            services_dict[category_name].append(subcategory_name)

        return dict(services_dict)

    def _get_certification_info(self, vendor):
        """Get certification information"""
        data = []
        certificates = LicenseAndCertificate.objects.filter(
            user_id=vendor.user_id, profile_type='vendor', document_type='insurance_certificate'
        )
        for certificate in certificates:
            cert_data = {
                'name': unsnake_case(certificate.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(certificate.document.name),
            }
            data.append(cert_data)

        certificates = LicenseAndCertificate.objects.filter(
            user_id=vendor.user_id, profile_type='vendor', document_type='other_certificate'
        )
        for certificate in certificates:
            cert_data = {
                'name': unsnake_case(certificate.document.name.split('/')[-1].split('.')[0]),
                'url': get_presigned_url(certificate.document.name),
            }
            data.append(cert_data)
        return data


class BulkVendorInviteAPIView(APIView):
    parser_classes = [MultiPartParser]
    serializer_class = BulkVendorInviteSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return CustomResponse({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        vendors_invited = list()
        all_errors = list()
        all_vendors = serializer.validated_data
        for vendor in all_vendors:
            email = vendor.get('email')
            role = vendor.get('role')
            first_name = vendor.get('first_name')
            last_name = vendor.get('last_name')

            if not serializer.is_valid():
                all_errors.append(serializer.errors)
                continue

            if Vendor.objects.filter(user_id__email=email).exists():
                all_errors.append(Error.VENDOR_ALREADY_EXISTS_V2.format(email))
                continue

            if VendorInvitation.objects.filter(email=email, sender=request.user, role=role).exists():
                if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, accepted=True).exists():
                    all_errors.append(Error.VENDOR_INVITATION_ALREADY_ACCEPTED.format(email, role))
                    continue
                if VendorInvitation.objects.filter(email=email, sender=request.user, role=role, expired_at__gte=timezone.now()).exists():
                    all_errors.append(Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role))
                    continue
                if VendorInvitation.objects.filter(
                    email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False
                ).exists():
                    VendorInvitation.objects.filter(
                        email=email, sender=request.user, role=role, expired_at__lte=timezone.now(), accepted=False
                    ).delete()

            try:
                invitation = VendorInvitation.objects.create(
                    sender=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    role=role,
                    expired_at=timezone.now() + timedelta(days=5),
                )

                email_variables = {
                    'VENDOR_FIRST_NAME': first_name,
                    'VENDOR_LAST_NAME': last_name,
                    'VENDOR_ROLE': role,
                    'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?vendor=true&invitation_id={invitation.id}",
                }

                send_email_(email, email_variables, 'INVITE-VENDOR')

                vendors_invited.append(email)

            except Exception as e:
                # Handle IntegrityError for duplicate invitations
                if 'UNIQUE constraint failed' in str(e) or 'duplicate key value' in str(e):
                    role_display = dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(role, role)
                    return all_errors.append(Error.VENDOR_INVITATION_ALREADY_SENT.format(email, role_display))
                all_errors.append(Error.VENDOR_INVITATION_SEND_FAILED.format(str(e)))
        data_ = Error.INVITATION_SENT_TO_EMAIL.format(', '.join(vendors_invited)) if vendors_invited else {}
        return CustomResponse(
            {"message": Success.VENDOR_INVITATION_SENT, "data": data_, "error": all_errors}, status=status.HTTP_201_CREATED
        )
