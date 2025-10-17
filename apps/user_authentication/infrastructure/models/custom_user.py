from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.user_authentication.domain.value_objects.enums import AuthMethod, SubscriptionPlan

from .custom_user_manager import CustomUserManager


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    otp_enable = models.BooleanField(default=False)
    otp = models.CharField(max_length=4, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    business_name = models.CharField(max_length=255, blank=True, null=True)
    auth_method = models.CharField(max_length=20, choices=AuthMethod.choices, default=AuthMethod.LOCAL)
    active_subscription = models.CharField(max_length=20, choices=SubscriptionPlan.choices, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    page_saved = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta:
        db_table = 'user'
