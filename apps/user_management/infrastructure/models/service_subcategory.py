from django.db import models

from .service_category import ServiceCategory


class ServiceSubCategory(models.Model):
    category_id = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='category')
    name = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)
