from django.conf import settings
from django.db import models

from apps.user_management.domain.services.dates import get_default_expiry_date

User = settings.AUTH_USER_MODEL


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
