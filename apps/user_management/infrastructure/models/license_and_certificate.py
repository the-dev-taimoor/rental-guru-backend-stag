from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class LicenseAndCertificate(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='license_and_certificates_user')
    profile_type = models.CharField(
        max_length=50, choices=[('property_owner', 'Property Owner'), ('vendor', 'Vendor')], blank=True, null=True
    )
    document = models.FileField(upload_to='documents/licenses_and_certificates/')
    document_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)
