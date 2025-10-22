from django.db import models

from .amenity import Amenity


class PropertyTypeAndAmenity(models.Model):
    sub_amenities = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='sub_amenities')
    property_type = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
