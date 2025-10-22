from django.db import models


class Amenity(models.Model):
    amenity = models.CharField(max_length=100)
    sub_amenity = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
