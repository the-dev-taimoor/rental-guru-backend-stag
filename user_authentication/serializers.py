import re
from random import choices

import pandas as pd
from io import BytesIO
from django.utils import timezone
from collections import defaultdict

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError
from properties.exceptions import CustomValidationError
from .models import (PropertyOwner, KYCRequest, Vendor, VendorServices, ServiceSubCategory, VendorInvitation,
                     LicenseAndCertificates, Tenant, TenantInvitation, Agreements)
from rental_guru.utils import get_presigned_url, unsnake_case, snake_case
from rental_guru.constants import Error


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=True)

    invitation_id = serializers.IntegerField(required=False)
    invitation_role = serializers.CharField(required=False)

    class Meta:
        model = get_user_model()
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'confirm_password', 'phone_number',
                  'otp_enable', 'email_verified', 'page_saved', 'invitation_id', 'invitation_role']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate(self, data):
        """
        Validate that the password and confirm password match.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = get_user_model().objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data['phone_number']
        )

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.username = validated_data['email']
        user.save()
        return user


class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    is_superuser = serializers.BooleanField(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        is_superuser = attrs.get("is_superuser", False)

        user = get_user_model().objects.filter(email=email, email_verified=True, is_superuser=is_superuser).first()
        if user is None:
            if is_superuser:
                raise NotFound("Not an admin user.")
            raise NotFound("User not found.")
        if not user.email_verified:
            raise serializers.ValidationError({
                "email": "Email not verified."
            })

        if not user.check_password(password):
            raise serializers.ValidationError({
            "password": "Incorrect password."
        })
        return user


class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=['SIGNUP', 'FORGOT-PASSWORD', 'SEND-OTP'], required=True, error_messages={
        'invalid_choice': 'It must be either "SIGNUP", "FORGOT-PASSWORD" or "SEND-OTP".'
    })


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class OTPEnableSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.BooleanField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=20,
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    def validate_new_password(self, value):
        """
        Validate the new password based on the given criteria.
        """
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one uppercase letter.'})

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one lowercase letter.'})

        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one number.'})

        if not re.search(r'[@$!%*?&]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one special character.'})

        return value

    def validate(self, data):
        """
        Ensure the new password and confirm password match.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data


class PropertyOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwner
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.profile_image_path.name:
            rep["profile_image_path"] = get_presigned_url(instance.profile_image_path.name)
        return rep


class KYCVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCRequest
        fields = ['user_id', 'id_type', 'front_image', 'back_image', 'notes']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.front_image.name:
            rep["front_image"] = get_presigned_url(instance.front_image.name)
        if instance.back_image.name:
            rep["back_image"] = get_presigned_url(instance.back_image.name)
        return rep

    def validate_user_id(self, value):
        try:
            existing_kyc = KYCRequest.objects.get(user_id=value)
            if existing_kyc.status == 'rejected':
                existing_kyc.delete()
            else:
                raise serializers.ValidationError("You have already submitted a KYC request.")
        except KYCRequest.DoesNotExist:
            pass
        return value


class KYCRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCRequest
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.front_image.name:
            rep["front_image"] = get_presigned_url(instance.front_image.name)
        if instance.back_image.name:
            rep["back_image"] = get_presigned_url(instance.back_image.name)
        return rep


class VendorProfileSerializer(serializers.ModelSerializer):
    services_offered = serializers.JSONField(write_only=True)
    services = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.profile_image_path.name:
            rep["profile_image_path"] = get_presigned_url(instance.profile_image_path.name)
        return rep

    def get_services(self, obj):
        vendor_services = VendorServices.objects.filter(user_id=obj.user_id) \
            .select_related('category_id', 'subcategory_id')

        category_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            category_dict[category_name].append(subcategory_name)

        return dict(category_dict)

    def create(self, validated_data):
        services_offered = validated_data.pop('services_offered', [])
        instance = super().create(validated_data)

        user = validated_data.get('user_id')
        VendorServices.objects.filter(user_id=user).delete()

        for subcat_id in services_offered:
            try:
                subcategory = ServiceSubCategory.objects.get(id=subcat_id)
            except ServiceSubCategory.DoesNotExist:
                continue

            VendorServices.objects.create(
                user_id=user,
                category_id=subcategory.category_id,
                subcategory_id=subcategory
            )
        return instance


class TenantProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenant
        fields = '__all__'

    def validate_investment_preferences(self, value):
        """
        Validate that investment_preferences contains only valid choices
        """
        if value is None:
            return value

        if not isinstance(value, list):
            raise serializers.ValidationError("Investment preferences must be a list.")

        valid_choices = [choice[0] for choice in Tenant.INVESTMENT_PREFERENCES_CHOICES]

        for preference in value:
            if preference not in valid_choices:
                raise serializers.ValidationError(
                    f"'{preference}' is not a valid investment preference. "
                    f"Valid choices are: {', '.join(valid_choices)}"
                )

        return list(dict.fromkeys(value))


class LicenseAndCertificatesSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = LicenseAndCertificates
        fields = ['id', 'document', 'title']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
            rep["title"] = unsnake_case(instance.document.name.split('/')[-1].split('.')[0])
        return rep

    def get_title(self, instance):
        return unsnake_case(instance.document.name.split('/')[-1].split('.')[0])


class SelectRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['property_owner', 'vendor', 'tenant'], required=True)


class VendorInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorInvitation
        fields = ['first_name', 'last_name', 'email', 'role']


class VendorInvitationBlockSerializer(serializers.Serializer):
    invitation_id = serializers.IntegerField(required=True)
    blocked = serializers.BooleanField(required=True)


class TenantInvitationSerializer(serializers.ModelSerializer):
    lease_agreement = serializers.FileField(required=True)
    class Meta:
        model = TenantInvitation
        fields = ['first_name', 'last_name', 'email', 'assignment_type', 'assignment_id', 'tenant_type',
                 'lease_amount', 'security_deposit', 'lease_start_date', 'lease_end_date', 'lease_agreement']

    def validate(self, attrs):
        assignment_type = attrs.get('assignment_type')
        assignment_id = attrs.get('assignment_id')

        if assignment_type == 'property':
            from properties.models import Property
            try:
                Property.objects.get(id=assignment_id)
            except Property.DoesNotExist:
                raise serializers.ValidationError("Property with this ID does not exist.")
        elif assignment_type == 'unit':
            from properties.models import Unit
            try:
                Unit.objects.get(id=assignment_id)
            except Unit.DoesNotExist:
                raise serializers.ValidationError("Unit with this ID does not exist.")
        else:
            raise serializers.ValidationError("assignment_type must be either 'unit' or 'property'.")

        return attrs


class InvitationAgreementSerializer(serializers.Serializer):
    """
    Serializer for updating invitation agreement status and signed agreement file.
    """
    invitation_id = serializers.IntegerField(required=True)
    agreed = serializers.BooleanField(required=True)
    signed_agreement = serializers.FileField(required=True)

    def validate_agreed(self, value):
        if value is not True:
            raise serializers.ValidationError(Error.AGREEMENT_REQUIRED)
        return value


class InvitationAcceptanceSerializer(serializers.Serializer):
    """
    Serializer for accepting or rejecting invitations.
    """
    invitation_id = serializers.IntegerField(required=True)
    accept = serializers.BooleanField(required=True)
    vendor = serializers.BooleanField(required=False, default=False)
    tenant = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        vendor = attrs.get('vendor', False)
        tenant = attrs.get('tenant', False)

        if not vendor and not tenant:
            raise serializers.ValidationError(Error.INVITATION_TYPE_REQUIRED)

        if vendor and tenant:
            raise serializers.ValidationError(Error.INVALID_INVITATION_TYPE)

        return attrs


class LeaseManagementSerializer(serializers.Serializer):
    """
    Serializer for managing lease agreements (end or renew).
    """
    invitation_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(choices=['end', 'renew'], required=True)
    lease_start_date = serializers.DateField(required=False)
    lease_end_date = serializers.DateField(required=False)
    rent_amount = serializers.IntegerField(required=False)
    security_deposit = serializers.IntegerField(required=False)
    lease_agreement = serializers.FileField(required=False)


    def validate(self, attrs):
        action = attrs.get('action')
        lease_end_date = attrs.get('lease_end_date')
        lease_start_date = attrs.get('lease_start_date')
        rent_amount = attrs.get('rent_amount')
        lease_agreement = attrs.get('lease_agreement')

        if action == 'renew':
            if not lease_start_date:
                raise serializers.ValidationError(Error.LEASE_START_DATE_REQUIRED)
            if not lease_end_date:
                raise serializers.ValidationError(Error.LEASE_END_DATE_REQUIRED)
            if not rent_amount:
                raise serializers.ValidationError(Error.RENT_AMOUNT_REQUIRED)
            if not lease_agreement:
                raise serializers.ValidationError(Error.LEASE_AGREEMENT_REQUIRED)

        return attrs


class VendorBasicInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor basic information tab"""
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user_id.phone_number', read_only=True)
    email = serializers.CharField(source='user_id.email', read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'full_name', 'phone_number', 'email', 'years_of_experience',
            'availability', 'emergency_services', 'languages', 'insurance_coverage',
            'vendor_role'
        ]

    def get_full_name(self, obj):
        user = obj.user_id
        return f"{user.first_name} {user.last_name}".strip()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Convert boolean fields to user-friendly text
        rep['availability'] = 'Available' if instance.availability else 'Not Available'
        rep['emergency_services'] = 'Yes' if instance.emergency_services else 'No'
        rep['insurance_coverage'] = 'Yes' if instance.insurance_coverage else 'No'

        # Format years of experience
        if instance.years_of_experience:
            rep['years_of_experience'] = f"{instance.years_of_experience} years"

        return rep


class VendorBusinessInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor business information tab"""

    class Meta:
        model = Vendor
        fields = [
            'business_name', 'business_website', 'business_address',
            'business_type', 'company_registration_number', 'registration_type'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.business_license.name:
            rep["business_license"] = get_presigned_url(instance.business_license.name)
        return rep


class VendorServicesInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor services information tab"""
    services = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['services', 'service_area', 'description']

    def get_services(self, obj):
        vendor_services = VendorServices.objects.filter(user_id=obj.user_id) \
            .select_related('category_id', 'subcategory_id')

        category_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            category_dict[category_name].append(subcategory_name)

        return dict(category_dict)


class VendorCertificationInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor certification information tab"""

    class Meta:
        model = Vendor
        fields = ['insurance_coverage', 'emergency_contact']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.insurance_certificates.name:
            rep["insurance_certificates"] = get_presigned_url(instance.insurance_certificates.name)
        if instance.other_certificates.name:
            rep["other_certificates"] = get_presigned_url(instance.other_certificates.name)
        return rep


class VendorJobsInfoSerializer(serializers.Serializer):
    """Serializer for vendor jobs information tab"""
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    jobs_completed = serializers.IntegerField(default=0)
    active_jobs = serializers.IntegerField(default=0)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, default=0)


class VendorPaymentsInfoSerializer(serializers.Serializer):
    """Serializer for vendor payments information tab"""
    payment_method = serializers.CharField(default="Not Set")
    bank_account = serializers.CharField(default="Not Set")
    payment_history = serializers.ListField(default=list)


class VendorDetailsByInvitationSerializer(serializers.Serializer):
    """Main serializer that combines all vendor information tabs"""
    invitation_info = serializers.SerializerMethodField()
    basic_info = VendorBasicInfoSerializer(read_only=True)
    business_info = VendorBusinessInfoSerializer(read_only=True)
    services_info = VendorServicesInfoSerializer(read_only=True)
    certification_info = VendorCertificationInfoSerializer(read_only=True)
    jobs_info = VendorJobsInfoSerializer(read_only=True)
    payments_info = VendorPaymentsInfoSerializer(read_only=True)

    def get_invitation_info(self, obj):
        invitation = obj.get('invitation')
        if invitation:
            return {
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'role': invitation.role,
                'role_display': dict(VendorInvitation.VENDOR_ROLE_CHOICES).get(invitation.role, invitation.role),
                'accepted': invitation.accepted,
                'blocked': invitation.blocked,
                'created_at': invitation.created_at,
                'updated_at': invitation.updated_at
            }
        return None


class InvitationDetailsSerializer(serializers.Serializer):
    """
    Unified serializer for both vendor and tenant invitation details.
    Returns invitation information without requiring authentication.
    """

    def to_representation(self, instance):
        """
        Convert invitation instance to dictionary representation.
        Handles both VendorInvitation and TenantInvitation models.
        """
        if hasattr(instance, 'role'):  # VendorInvitation
            return {
                'id': instance.id,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'sender': instance.sender.email,
                'sender_name': f"{instance.sender.first_name} {instance.sender.last_name}".strip(),
                'expired_at': instance.expired_at
            }
        elif hasattr(instance, 'tenant_type'):  # TenantInvitation
            lease_agreement_url = None
            agreement = Agreements.objects.filter(invitation=instance.id).order_by('-created_at').first()
            if agreement.lease_agreement and agreement.lease_agreement.name:
                lease_agreement_url = get_presigned_url(agreement.lease_agreement.name)

            return {
                'id': instance.id,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'sender': instance.sender.email,
                'sender_name': f"{instance.sender.first_name} {instance.sender.last_name}".strip(),
                'lease_start_date': instance.lease_start_date,
                'lease_end_date': instance.lease_end_date,
                'lease_agreement_url': lease_agreement_url,
                'lease_ended': True if instance.lease_end_date <= timezone.now().date() else False,
                'expired_at': instance.expired_at
            }
        else:
            return {}


class BulkVendorInviteSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate(self, attrs):
        if not (attrs['file'].name.endswith('.xlsx') or attrs['file'].name.endswith('.csv')):
            raise CustomValidationError("File must be in CSV/XLSX format")

        try:
            file_data = attrs['file'].read()
            if attrs['file'].name.endswith('.xlsx'):
                xls = pd.ExcelFile(BytesIO(file_data))
                df = pd.read_excel(xls, sheet_name=0)
            else:
                df = pd.read_csv(BytesIO(file_data), skip_blank_lines=True)
            df.dropna(how='all', inplace=True)

            df.columns = df.columns.str.strip()
            expected_columns = ['First Name', 'Last Name', 'Email', 'Role']
            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                raise CustomValidationError(f"Missing columns: {', '.join(missing_cols)}")

            data = []
            for _, row in df.iterrows():
                role_ = snake_case(row['Role'])
                vendor_data = {
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'email': row['Email'],
                    'role': role_
                }
                if role_ not in dict(VendorInvitation.VENDOR_ROLE_CHOICES):
                    raise CustomValidationError(f"Invalid role: {row['Role']}")
                data.append(vendor_data)


            return data

        except Exception as e:
            raise CustomValidationError(e)


class ResendInvitationSerializer(serializers.Serializer):
    invitation_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(choices=['vendor', 'tenant'], required=True)
