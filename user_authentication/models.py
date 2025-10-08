import os
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework.exceptions import APIException


User = settings.AUTH_USER_MODEL


def get_default_expiry_date():
    """Return default expiry date (5 days from now)"""
    return timezone.now() + timedelta(days=5)


class CustomUserManager(UserManager):

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if email:
            users = CustomUser.objects.filter(email=email)
            email_verified = CustomUser.objects.filter(email=email).values_list('email_verified', flat=True).first()
            if users.exists() and email_verified:
                raise APIException('Email already Exists.')
            else:
                users.delete()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    class SubscriptionPlan(models.TextChoices):
        BASIC = 'basic'
        ENTERPRISE = 'enterprise'
        PRO = 'pro'
    class AuthMethod(models.TextChoices):
        FACEBOOK = 'facebook'
        LINKEDIN = 'linkedin'
        GOOGLE = 'google'
        APPLE = 'apple'
        LOCAL = 'local'
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    otp_enable = models.BooleanField(default=False)
    otp = models.CharField(max_length=4, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    business_name = models.CharField(max_length=255, blank=True, null=True)
    auth_method = models.CharField(
        max_length=20,
        choices=AuthMethod.choices,
        default=AuthMethod.LOCAL
    )
    active_subscription = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        blank=True, null=True
    )
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    page_saved = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta:
        db_table = 'user'


class Role(models.Model):
    class RoleType(models.TextChoices):
        owner = 'property_owner'
        vendor = 'vendor'
        tenant = 'tenant'
    user_id  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_user')

    role = models.CharField(
        max_length=20,
        choices=RoleType.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.user_id

    class Meta:
        unique_together = ('user_id', 'role')


class PropertyOwner(models.Model):
    class RegistrationType(models.TextChoices):
        individual = 'individual'
        business = 'business'
    user_id  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='property_owner_user')

    profile_image_path = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    registration_type = models.CharField(
        max_length=20,
        choices=RegistrationType.choices,
        default=RegistrationType.individual)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    business_website = models.CharField(max_length=100, blank=True, null=True)
    business_address = models.CharField(max_length=100, blank=True, null=True)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True)

    page_saved = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.user_id


class KYCRequest(models.Model):
    class IDType(models.TextChoices):
        CNIC = 'cnic'
        PASSPORT = 'passport'
        DRIVING_LICENSE = 'driving_license'
    class KYCStatus(models.TextChoices):
        PENDING = 'pending'
        APPROVED = 'approved'
        REJECTED = 'rejected'
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_user')
    id_type = models.CharField(max_length=50, choices=IDType.choices)
    front_image = models.FileField(upload_to='kyc_docs/')
    back_image = models.FileField(upload_to='kyc_docs/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING
    )
    notes = models.TextField(default=None, blank=True, null=True)
    reviewed_at = models.DateField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"KYC Details for {self.user_id}"


class Vendor(models.Model):
    class RegistrationType(models.TextChoices):
        individual = 'individual'
        business = 'business'
    user_id  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_user')

    vendor_role = models.CharField(max_length=50, blank=True, null=True)
    profile_image_path = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    registration_type = models.CharField(
        max_length=20,
        choices=RegistrationType.choices,
        default=RegistrationType.individual)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    business_website = models.CharField(max_length=100, blank=True, null=True)
    business_address = models.CharField(max_length=100, blank=True, null=True)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True)

    service_area = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.CharField(max_length=50, blank=True, null=True)
    availability = models.BooleanField(default=False)
    daily_availability = models.JSONField(blank=True, null=True)
    emergency_services = models.BooleanField(default=False)
    emergency_contact = models.CharField(max_length=10, blank=True, null=True)
    languages = models.CharField(max_length=100, blank=True, null=True)
    insurance_coverage = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    page_saved = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.user_id


class LicenseAndCertificates(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='license_and_certificates_user')
    profile_type = models.CharField(max_length=50, choices=[('property_owner', 'Property Owner'), ('vendor', 'Vendor')], blank=True, null=True)
    document = models.FileField(upload_to='documents/licenses_and_certificates/')
    document_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class ServiceCategory(models.Model):
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class ServiceSubCategory(models.Model):
    category_id = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='category')
    name = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class VendorServices(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_vendor')
    category_id = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='service_category')
    subcategory_id = models.ForeignKey(ServiceSubCategory, on_delete=models.CASCADE, related_name='service_subcategory')

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class VendorInvitation(models.Model):
    VENDOR_ROLE_CHOICES = [
        ('personal_training', 'Personal Training'),
        ('home_cleaning', 'Home Cleaning'),
        ('personal_chef', 'Personal Chef'),
        ('yoga_instruction', 'Yoga Instruction'),
        ('electrical_services', 'Electrical Services'),
        ('hvac_technician', 'HVAC Technician'),
        ('landscaping', 'Landscaping'),
        ('pest_control', 'Pest Control'),
        ('appliance_repair', 'Appliance Repair'),
        ('security_services', 'Security Services'),
        ('painting_renovation', 'Painting & Renovation'),
        ('general_handyman', 'General Handyman'),
        ('moving_services', 'Moving Services'),
        ('it_network_setup', 'IT & Network Setup'),
        ('furniture_assembly', 'Furniture Assembly'),
        ('window_cleaning', 'Window Cleaning'),
        ('pool_maintenance', 'Pool Maintenance'),
        ('carpet_cleaning', 'Carpet Cleaning'),
        ('elderly_care_services', 'Elderly Care Services'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_invitations_sent')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=100, choices=VENDOR_ROLE_CHOICES)
    accepted = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(blank=True, null=True, default=get_default_expiry_date)

    class Meta:
        unique_together = ('email', 'role', 'sender')  # Prevent duplicate invitations for same email+role

    def __str__(self):
        return f"Vendor invitation to {self.first_name} {self.last_name} ({self.email}) for {self.role}"


class Tenant(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_user')
    job_title = models.CharField(max_length=50, blank=True, null=True)
    EMPLOYMENT_STATUS_CHOICES = [
        ('full-time', 'Full-Time'),
        ('part-time', 'Part-Time'),
        ('self-employed', 'Self-Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('retired', 'Retired')
    ]
    employment_status = models.CharField(max_length=20, blank=True, null=True, choices=EMPLOYMENT_STATUS_CHOICES)
    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    industry = models.CharField(max_length=20, blank=True, null=True, choices=INDUSTRY_CHOICES)
    INCOME_RANGE_CHOICES = [
        ('<$50,000', '<$50,000'),
        ('$50,000-$70,000', '$50,000-$70,000'),
        ('$70,000-$90,000', '$70,000-$90,000'),
        ('>$90,000', '>$90,000'),
    ]
    income_range = models.CharField(max_length=30, blank=True, null=True, choices=INCOME_RANGE_CHOICES)
    mortgage_amount = models.CharField(max_length=50, blank=True, null=True)
    CREDIT_SCORE_RANGE_CHOICES = [
        ('500-600', '500-600'),
        ('600-700', '600-700'),
        ('700-750', '700-750'),
        ('750+', '750+'),
    ]
    credit_score_range = models.CharField(max_length=15, blank=True, null=True, choices=CREDIT_SCORE_RANGE_CHOICES)
    debt_to_income_ratio = models.CharField(max_length=25, blank=True, null=True)
    INVESTMENT_PREFERENCES_CHOICES = [
        ('stocks', 'Stocks'),
        ('real_estate', 'Real Estate'),
        ('cryptocurrencies', 'Cryptocurrencies'),
        ('bonds', 'Bonds'),
    ]
    investment_preferences = models.JSONField(blank=True, null=True, default=list)
    PROPERTY_TYPE_CHOICES = [
        ('renting', 'Renting'),
        ('owning', 'Owning'),
        ('living_with_family/friends', 'Living with Family/Friends'),
    ]
    property_type = models.CharField(max_length=30, blank=True, null=True, choices=PROPERTY_TYPE_CHOICES)
    LENGTH_OF_STAY_CHOICES = [
        ('less_than_1_year', 'Less than 1 year'),
        ('1-3 years', '1-3 years'),
        ('3-5 years', '3-5 years'),
        ('5+ years', '5+ years'),
    ]
    length_of_stay = models.CharField(max_length=20, blank=True, null=True, choices=LENGTH_OF_STAY_CHOICES)
    UTILITY_COST_ESTIMATES_CHOICES = [
        ('<$100', '<$100'),
        ('$100-$200', '$100-$200'),
        ('$200-$500', '$200-$500'),
        ('>$300', '>$300'),
    ]
    utility_cost_estimates = models.CharField(max_length=20, blank=True, null=True, choices=UTILITY_COST_ESTIMATES_CHOICES)
    lease_term = models.IntegerField(blank=True, null=True)
    PREFERRED_RENTAL_PRICE_RANGE_CHOICES = [
        ('$1000-$1500', '$1000-$1500'),
        ('$1500-$2000', '$1500-$2000'),
        ('$2000-$2500', '$2000-$2500'),
        ('$2500+', '$2500+'),
    ]
    preferred_rental_price_range = models.CharField(max_length=20, blank=True, null=True, choices=PREFERRED_RENTAL_PRICE_RANGE_CHOICES)
    current_home_value = models.CharField(max_length=50, blank=True, null=True)
    INTEREST_IN_MOVING_CHOICES = [
        ('within_6_months', 'Yes, in the next 6 months'),
        ('not_planning_to_move', 'No, not planning to move'),
    ]
    interest_in_moving = models.CharField(max_length=50, blank=True, null=True, choices=INTEREST_IN_MOVING_CHOICES)
    LATE_BILL_PAYMENT_HISTORY_CHOICES = [
        ('never', 'Never Missed a Payment'),
        ('occasionally', 'Occasionally Late (1-2 times a year)'),
        ('frequently', 'Frequently Late (3+ times a year)'),
    ]
    late_bill_payment_history = models.CharField(max_length=50, blank=True, null=True, choices=LATE_BILL_PAYMENT_HISTORY_CHOICES)
    SPENDING_HABITS_CHOICES = [
        ('strict', 'I stick to a strict budget'),
        ('moderate', 'I track spending but make occasional impulse buys'),
        ('flexible', 'I spend freely and adjust as needed'),
    ]
    spending_habits = models.CharField(max_length=50, blank=True, null=True, choices=SPENDING_HABITS_CHOICES)
    monthly_budget_allocations = models.CharField(max_length=50, blank=True, null=True)
    FINANCIAL_GOALS_CHOICES = [
        ('pay_off_debt', 'Pay Off Debt'),
        ('build_an_emergency_fund', 'Build an Emergency Fund'),
        ('increase_investments', 'Increase Investments'),
    ]
    financial_goals = models.CharField(max_length=50, blank=True, null=True, choices=FINANCIAL_GOALS_CHOICES)
    ai_for_suggestions = models.BooleanField(default=False)

    page_saved = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Tenant {self.user_id}"


class TenantInvitation(models.Model):
    TENANT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('family', 'Business'),
        ('shared_housing', 'Shared Housing'),
        ('small_business', 'Small Business'),
        ('corporate_office', 'Corporate Office'),
        ('retail_store', 'Retail Store'),
        ('restaurant', 'Restaurant'),
        ('warehouse', 'Warehouse'),
    ]

    ASSIGNMENT_TYPE_CHOICES = [
        ('unit', 'Unit'),
        ('property', 'Property'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_invitations_sent')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='unit')
    assignment_id = models.PositiveIntegerField(default=None)
    tenant_type = models.CharField(max_length=30, choices=TENANT_TYPE_CHOICES)
    lease_amount = models.IntegerField()
    security_deposit = models.IntegerField(blank=True, null=True)
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()

    accepted = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    agreed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('email', 'tenant_type', 'sender', 'assignment_type', 'assignment_id')  # Prevent duplicate invitations for same email+tenant_type+assignment

    def __str__(self):
        return f"Tenant invitation to {self.first_name} {self.last_name} ({self.email}) for {self.tenant_type}"

    @property
    def assigned_object(self):
        """Get the assigned property or unit object"""
        if self.assignment_type == 'property':
            from properties.models import Property
            try:
                return Property.objects.get(id=self.assignment_id)
            except Property.DoesNotExist:
                return None
        elif self.assignment_type == 'unit':
            from properties.models import Unit
            try:
                return Unit.objects.get(id=self.assignment_id)
            except Unit.DoesNotExist:
                return None
        return None


class Agreements(models.Model):
    invitation = models.ForeignKey(TenantInvitation, on_delete=models.CASCADE, related_name='agreements')
    lease_agreement = models.FileField(upload_to='tenant_agreements/')
    signed_agreement = models.FileField(upload_to='tenant_signed_agreements/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agreement for {self.invitation}"
