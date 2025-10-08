# apps/users/domain/value_objects/user_enums.py

from django.db import models

class SubscriptionPlan(models.TextChoices):
    BASIC = 'basic', 'Basic'
    ENTERPRISE = 'enterprise', 'Enterprise'
    PRO = 'pro', 'Pro'


class AuthMethod(models.TextChoices):
    FACEBOOK = 'facebook', 'Facebook'
    LINKEDIN = 'linkedin', 'LinkedIn'
    GOOGLE = 'google', 'Google'
    APPLE = 'apple', 'Apple'
    LOCAL = 'local', 'Local'
