from django.db import models

from .cost_fee_category import CostFeeCategory


class CostFee(models.Model):
    category = models.ForeignKey(CostFeeCategory, on_delete=models.CASCADE, related_name='fees')
    fee_name = models.CharField(max_length=100)
    payment_frequency_by_choices = [
        ('one_time', "One Time"),
        ('monthly', "Monthly"),
        ('per_use', "Per Use"),
        ('quarterly', "Quarterly"),  # university_housing
        ('yearly', "Yearly"),  # university_housing
    ]
    payment_frequency = models.CharField(max_length=50, choices=payment_frequency_by_choices)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fee_type_by_choices = [
        ('flat_fee', "Flat Fee"),
        ('flat_fee_per_item', "Flat Fee Per Item"),
        ('fee_range', "Fee Range"),
    ]
    fee_type = models.CharField(max_length=50, choices=fee_type_by_choices)
    required_status_choices = [
        ('in_rent', 'Included in base rent'),
        ('required', 'Required'),
        ('optional', 'Optional'),
    ]
    is_required = models.CharField(max_length=50, choices=required_status_choices)
    refundable_status_choices = [
        ('non_refundable', 'Non-refundable'),
        ('partially_refundable', 'Partially refundable'),
        ('refundable', 'Refundable'),
    ]
    refundable_status = models.CharField(max_length=50, blank=True, null=True, choices=refundable_status_choices)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('category', 'fee_name')

    def __str__(self):
        return f"{self.fee_name} in {self.category.category_name}"
