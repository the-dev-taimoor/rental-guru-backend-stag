from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

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