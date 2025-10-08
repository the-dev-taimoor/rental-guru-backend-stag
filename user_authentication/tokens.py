from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import BlacklistMixin, Token


class CustomAccessToken(BlacklistMixin, Token):
    token_type = 'access'
    lifetime = api_settings.ACCESS_TOKEN_LIFETIME
