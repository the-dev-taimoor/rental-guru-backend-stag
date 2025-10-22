from django.db import models

from .property import Property
from .unit import Unit


class CostFeeCategory(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_cost_fee_categories')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_cost_fee_categories', null=True, default=None)
    category_name = models.CharField(max_length=100)  # e.g., Parking, Utilities, Other Categories

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category_name} costs for {self.property.name}"
