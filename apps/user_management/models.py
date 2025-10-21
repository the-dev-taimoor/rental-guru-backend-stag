from apps.user_management.infrastructure.models.custom_user import CustomUser
from apps.user_management.infrastructure.models.custom_user_manager import CustomUserManager

# we need this because CustomUser and CustomUserManager are wrappers of Django's built in ORM classes and
# it looks for those wrappers inside the app_name/models by default
__all__ = ["CustomUser", "CustomUserManager"]
