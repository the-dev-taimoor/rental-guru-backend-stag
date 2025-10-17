from rest_framework.exceptions import APIException

from apps.user_authentication.infrastructure.models.custom_user import CustomUser


# this is not being used anywhere
def create_user(email, password, **extra_fields):
    existing_user = CustomUser.objects.filter(email=email).first()
    if existing_user and existing_user.email_verified:
        raise APIException('Email already exists.')

    if existing_user:
        existing_user.delete()

    user = CustomUser(email=email, **extra_fields)
    user.set_password(password)
    user.save()
    return user
