from django.contrib.auth import get_user_model
from django.db import models

from .property import Property

User = get_user_model()


class OwnerInfo(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_owned')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_detail')  # one who is inviting
    email = models.EmailField()
    percentage = models.CharField(max_length=10)
    emergency_person = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)

    registered = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'owner', 'email')

    def __str__(self):
        return f"Owner info for {self.property.name}"
