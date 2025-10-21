from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.property_management"
    migrations_module = 'apps.property_management.infrastructure.migrations'
