from django.db import models

from .tenant_invitation import TenantInvitation


class Agreement(models.Model):
    invitation = models.ForeignKey(TenantInvitation, on_delete=models.CASCADE, related_name='agreements')
    lease_agreement = models.FileField(upload_to='tenant_agreements/')
    signed_agreement = models.FileField(upload_to='tenant_signed_agreements/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agreement for {self.invitation}"
