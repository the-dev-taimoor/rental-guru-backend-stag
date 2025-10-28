from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shared"

    def ready(self):
        # Pre-initialize S3 client when app starts
        from apps.shared.infrastructure.services.s3_service import S3Service

        S3Service()  # this will initialize immediately
