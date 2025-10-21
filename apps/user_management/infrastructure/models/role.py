from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Role(models.Model):
    class RoleType(models.TextChoices):
        owner = 'property_owner'
        vendor = 'vendor'
        tenant = 'tenant'

    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_user')

    role = models.CharField(max_length=20, choices=RoleType.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.user_id

    class Meta:
        unique_together = ('user_id', 'role')
