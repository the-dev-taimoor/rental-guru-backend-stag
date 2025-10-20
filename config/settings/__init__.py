import os

ENVIRONMENT = os.getenv('DJANGO_ENV', 'local')
if ENVIRONMENT == 'production':
    from .production import ProductionSettings as CurrentSettings
else:
    from .local import LocalSettings as CurrentSettings

# Apply settings from the chosen class to the global scope
for setting_name in dir(CurrentSettings):
    if not setting_name.startswith('__'):
        globals()[setting_name] = getattr(CurrentSettings, setting_name)
