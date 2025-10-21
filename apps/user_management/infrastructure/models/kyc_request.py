from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


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
    status = models.CharField(max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING)
    notes = models.TextField(default=None, blank=True, null=True)
    reviewed_at = models.DateField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"KYC Details for {self.user_id}"
