from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

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