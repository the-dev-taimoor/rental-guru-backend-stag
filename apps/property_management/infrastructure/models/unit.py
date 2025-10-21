from django.db import models

from .property import Property


class Unit(models.Model):
    status_by_choices = [
        ('vacant', "Vacant"),
        ('occupied', "Occupied"),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='unit_property')
    number = models.CharField(max_length=20)
    type = models.CharField(max_length=20)
    floor_number = models.CharField(max_length=20, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    beds = models.PositiveIntegerField(default=0)
    desks = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='vacant', choices=status_by_choices)

    other_amenities = models.JSONField(blank=True, null=True, help_text="List of other amenities")

    csv_upload = models.IntegerField(default=0)
    page_saved = models.IntegerField(default=1)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.number
