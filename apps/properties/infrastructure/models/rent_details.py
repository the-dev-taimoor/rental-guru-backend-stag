from django.db import models

from .property import Property
from .unit import Unit


class RentDetails(models.Model):
    rental_type_by_choices = [
        ('short_term', "Short-Term (Daily/Weekly)"),
        ('long_term', "Long-Term (Monthly/Annual)"),
        ('monthly_billing', "Monthly Billing"),  # university_housing
        ('semester_billing', "Semester Billing"),  # university_housing
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_rent_details')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_rent_details', null=True, default=None)
    # tenant FK needs to be here
    assigned_tenant = models.CharField(max_length=100, blank=True, null=True)
    rental_type = models.CharField(max_length=50, choices=rental_type_by_choices)
    semester = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('fall', "Fall"),
            ('spring', "Spring"),
            ('summer', "Summer"),
        ],
    )
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    lease_start_date = models.DateField(blank=True, null=True)
    lease_end_date = models.DateField(blank=True, null=True)
    promote_special_offer = models.BooleanField(default=False)
    offer_start_date = models.DateField(blank=True, null=True)
    offer_end_date = models.DateField(blank=True, null=True)
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'unit')

    def __str__(self):
        return f"Rent Details for {self.property.name}"
