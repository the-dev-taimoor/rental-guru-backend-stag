from django.db import models

from .amenitites import Amenities
from .property import Property
from .unit import Unit


class PropertyAssignedAmenities(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_amenities', null=True, default=None)
    sub_amenity = models.ForeignKey(Amenities, on_delete=models.CASCADE, related_name='assigned_sub_amenity')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Amenities for {self.property.name}"
