
from django.contrib.auth.models import  UserManager

#  this is not being used anywhere
class CustomUserManager(UserManager):
    pass
    # def _create_user(self, username, email, password, **extra_fields):
    #     """
    #     Create and save a user with the given username, email, and password.
    #     """
    #     if email:
    #         users = self.model.objects.filter(email=email)
    #         email_verified = users.values_list('email_verified', flat=True).first()

    #         if users.exists() and email_verified:
    #             raise APIException('Email already exists.')
    #         else:
    #             users.delete()

    #     user = self.model(email=email, **extra_fields)
    #     user.set_password(password)
    #     user.save(using=self._db)
    #     return user