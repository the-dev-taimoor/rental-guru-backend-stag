import os
from datetime import timedelta
from pathlib import Path

from dotenv import dotenv_values

# Load .env values
env_values = dotenv_values()


def get_env_value(key, default=None):
    return os.environ.get(key, env_values.get(key, default))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

log_directory = os.path.join(BASE_DIR, 'logs')
log_file = os.path.join(log_directory, 'error.log')


class BaseSettings:
    """
    Base Django settings class.
    Loads environment variables from .env and provides some defaults.
    """

    BASE_DIR = BASE_DIR
    LOG_DIR = log_directory
    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = get_env_value("DJANGO_SECRET_KEY")

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    ALLOWED_HOSTS = get_env_value("ALLOWED_ORIGINS").split(',')

    CSRF_TRUSTED_ORIGINS = get_env_value("CSRF_TRUSTED_ORIGINS").split(',')

    CORS_ALLOWED_ORIGINS = get_env_value("CORS_ORIGIN_WHITELIST").split(',')
    CORS_ALLOW_METHODS = (
        "DELETE",
        "GET",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    )

    CORS_ALLOW_CREDENTIALS = True

    # Application definition

    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "rest_framework",
        "rest_framework_simplejwt",
        "rest_framework_simplejwt.token_blacklist",
        "apps.user_management",
        "drf_yasg",
        "corsheaders",
        "storages",
        "apps.property_management",
        "apps.shared",
    ]

    MIGRATION_MODULES = {
        'property_management': 'apps.property_management.infrastructure.migrations',
        'user_management': 'apps.user_management.infrastructure.migrations',
    }

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
        'EXCEPTION_HANDLER': 'common.utils.custom_exception_handler',
    }

    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
        'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
        'ROTATE_REFRESH_TOKENS': False,
        'BLACKLIST_AFTER_ROTATION': False,
    }

    MIDDLEWARE = [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    ROOT_URLCONF = "config.urls"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ]

    WSGI_APPLICATION = "config.wsgi.application"

    # Database
    # https://docs.djangoproject.com/en/4.2/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': get_env_value('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': get_env_value('DB_NAME'),
            'USER': get_env_value('DB_USER'),
            'PASSWORD': get_env_value('DB_PASSWORD'),
            'HOST': get_env_value('DB_HOST'),
            'PORT': get_env_value('DB_PORT'),
        }
    }
    # Password validation
    # https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/4.2/topics/i18n/

    LANGUAGE_CODE = "en-us"

    TIME_ZONE = "UTC"

    USE_I18N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.2/howto/static-files/

    STATIC_URL = "static/"

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    AUTH_USER_MODEL = 'user_management.CustomUser'

    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'

    # drf-yasg Swagger settings to add Bearer auth in the UI
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header using the Bearer scheme. Example: "Bearer <token>"',
            }
        }
    }
    EMAIL_FILE_PATH = "./tmp/app-messages"
    # EMAIL_HOST = 'smtp.gmail.com'
    # EMAIL_PORT = 587
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = get_env_value("EMAIL_HOST_USER")
    # EMAIL_HOST_PASSWORD = get_env_value("EMAIL_HOST_PASSWORD")
    SITE_DOMAIN = get_env_value("SITE_DOMAIN")
    FRONTEND_DOMAIN = get_env_value("FRONTEND_DOMAIN")

    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

    AWS_ACCESS_KEY_ID = get_env_value("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_env_value("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = get_env_value("AWS_DEFAULT_REGION")
    AWS_S3_BUCKET_NAME = get_env_value("AWS_S3_BUCKET_NAME")
    AWS_S3_BASE_URL = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com"

    AWS_QUERYSTRING_AUTH = True
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

    ENV = get_env_value("ENV")
