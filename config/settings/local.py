from .base import BaseSettings
import os
import sys

class LocalSettings(BaseSettings):
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "detailed": {
                "format": "{asctime} [{levelname}] {name} (line:{lineno}) - {message}",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "[{levelname}] {message}",
                "style": "{",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "simple",
            },
            "file": {
                "level": "ERROR",
                "class": "logging.FileHandler",
                "filename": os.path.join(BaseSettings.LOG_DIR, "error.log"),
                "formatter": "detailed",
            },
        },

        "loggers": {
            # Django core logs (keep only warnings and above)
            "django": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": True,
            },
            # Requests (useful for catching view errors)
            "django.request": {
                "handlers": ["console", "file"],
                "level": "ERROR",
                "propagate": False,
            },
            # Database queries (set to INFO only if needed)
            "django.db.backends": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            # REST framework logs
            "rest_framework": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            # Your app-level logs (still detailed)
            "apps": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },

        # Root logger - only show high-level errors by default
        "root": {
            "handlers": ["console", "file"],
            "level": "ERROR",
        },
    }