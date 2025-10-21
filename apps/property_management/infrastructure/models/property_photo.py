from django.db import models

from .property import Property
from .unit import Unit


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_photos')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_photos', null=True, default=None)
    photo = models.ImageField(upload_to='property_photos/', max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Photo of {self.property.name}"
