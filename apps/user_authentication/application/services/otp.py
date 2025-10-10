import random
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.exceptions import APIException
from datetime import timedelta

from common.constants import email_templates, Error


logger = logging.getLogger('django')


def otp_email(user, action, template_variables=None):
    """
    Sends an OTP email to the user using a specified email template.
    Args:
        action: Key to select email template.
        template_variables: Variables for the template.
    """
    try:
        recipient_list = [user.email]
        otp_code = random.randint(1000, 9999)
        if settings.ENV == 'qa':
            otp_code = 1234

        variables = {'USER_FIRST_NAME': user.first_name, 'OTP_CODE': otp_code}
        if template_variables:
            template_variables.update(variables)
        else:
            template_variables = variables

        template = email_templates.get(action)
        subject = template.get('subject')
        duration = int(template.get('duration'))
        html_message = template.get('html_message').format(**template_variables)

        send_mail(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        user.otp = otp_code
        otp_expiry = timezone.now() + timedelta(minutes=duration)
        user.otp_expiry = otp_expiry
        user.save()
    except Exception as e:
        logger.error(str(e))
        raise APIException(Error.RESPONSE_VERIFICATION_EMAIL_ERROR)