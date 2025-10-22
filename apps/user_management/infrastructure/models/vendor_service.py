from django.conf import settings
from django.db import models

from .service_category import ServiceCategory
from .service_subcategory import ServiceSubCategory

User = settings.AUTH_USER_MODEL


class VendorService(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_vendor')
    category_id = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='service_category')
    subcategory_id = models.ForeignKey(ServiceSubCategory, on_delete=models.CASCADE, related_name='service_subcategory')

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)
