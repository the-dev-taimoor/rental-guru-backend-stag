# apps/properties/domain/services/dates.py

from datetime import timedelta

from django.utils import timezone


def get_default_expiry_date():
    """Return default expiry date (5 days from now)"""
    return timezone.now() + timedelta(days=5)
