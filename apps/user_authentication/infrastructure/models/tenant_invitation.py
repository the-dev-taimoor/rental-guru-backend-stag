from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

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
            from apps.properties.infrastructure.models import Property
            try:
                return Property.objects.get(id=self.assignment_id)
            except Property.DoesNotExist:
                return None
        elif self.assignment_type == 'unit':
            from apps.properties.infrastructure.models import Unit
            try:
                return Unit.objects.get(id=self.assignment_id)
            except Unit.DoesNotExist:
                return None
        return None