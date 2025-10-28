import logging
import os
import tempfile
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import Http404
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response as DRFResponse
from rest_framework.views import exception_handler, status
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.shared.infrastructure.services.s3_service import S3Service
from common.constants import Error, email_templates

logger = logging.getLogger('django')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    message = None

    # Safely extract error message
    if isinstance(exc, (Http404, IntegrityError)):
        error_ = exc.args[0]
    elif hasattr(exc, 'detail'):
        error_ = exc.detail
    else:
        # fallback for non-DRF exceptions like SwaggerGenerationError
        error_ = str(exc)

    error = flatten_errors(error_)

    if isinstance(exc, Http404):
        message = 'Not found.'
    elif isinstance(exc, InvalidToken):
        message = 'Invalid Token'
    elif isinstance(exc, NotFound):
        message = 'Not found.'
    elif isinstance(exc, ValidationError):
        message = 'Invalid Field.'
    elif isinstance(exc, IntegrityError):
        message = 'Invalid Value.'

    response_data = {
        'data': {},
        'error': error if error else None,
        'success': False,
        'message': message,
    }

    if response is not None:
        response.data = response_data
    else:
        response = DRFResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    return response


def flatten_errors(errors, field_name=None):
    """
    Recursively extracts and flattens the first error message from nested serializer errors.
    Replaces "This field is required." with a customized message including the field name.
    """
    if isinstance(errors, dict):
        messages = []
        for field, msgs in errors.items():
            field = field.replace('_', ' ')
            # If msgs is list or dict, recurse or flatten
            if isinstance(msgs, (list, dict)):
                # Flatten nested errors
                inner_message = flatten_errors(msgs)
                if 'this field' in inner_message or 'This field' in inner_message:
                    inner_message = inner_message.replace('this field', field).replace('This field', field)
                else:
                    if field == 'non field errors':
                        inner_message = inner_message.lower()
                    else:
                        inner_message = field + '; ' + inner_message.lower()
                messages.append(f"{inner_message}")
            else:
                # If msg is just string
                msgs = msgs.replace('this field', field).replace('This field', field)
                messages.append(f"{msgs}")
        return messages[0]
    elif isinstance(errors, list):
        messages = [flatten_errors(item) if isinstance(item, (list, dict)) else str(item) for item in errors]
        value = f"{field_name}; {messages[0]}" if field_name and field_name != 'non_field_errors' else messages[0]
        return value
    else:
        return str(errors)


def error_string(unit_errors_dict):
    error_messages = []
    for key, value in unit_errors_dict.items():
        if isinstance(value, dict):
            value_str = str(value)
        elif not isinstance(value, str):
            value_str = str(value)
        else:
            value_str = value

        error_messages.append(f"{key}: {value_str}")
    return ', '.join(error_messages)


class CustomAPIError(APIException):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CustomResponse(DRFResponse):
    def __init__(self, data_dict, *args, **kwargs):
        if isinstance(data_dict.get('error'), dict):
            error_dict = data_dict.get('error')
            # Check for non_field_errors first
            if 'non_field_errors' in error_dict and error_dict['non_field_errors']:
                data_dict['error'] = str(error_dict['non_field_errors'][0])
            # Check for other attributes if non_field_errors doesn't exist or is empty
            elif error_dict:
                # Get the first error from any field
                for field, errors in error_dict.items():
                    if errors:
                        if isinstance(errors, list):
                            data_dict['error'] = f"{field}: {errors[0]}"
                        else:
                            data_dict['error'] = f"{field}: {errors}"
                        break
                if isinstance(data_dict['error'], dict):
                    data_dict['error'] = str(error_dict)

        formatted_data = {
            'data': data_dict.get('data', {}),
            'error': data_dict.get('error', None),
            'success': data_dict.get('success', True),
            'message': data_dict.get('message', ''),
        }
        super().__init__(formatted_data, *args, **kwargs)


def get_presigned_url(key, expiration=3600, download=False, filename=None):
    """
    Generate a presigned URL for an S3 object.

    Args:
        key: The S3 object key
        expiration: URL expiration time in seconds (default: 3600)
        download: Whether to force download instead of in-browser display (default: False)
        filename: Custom filename for download (default: None, uses original filename)

    Returns:
        Presigned URL string
    """
    if key.startswith("http") or key.startswith("https"):
        return key

    s3 = S3Service()  # this reuses the same singleton instance

    params = {'Bucket': settings.AWS_S3_BUCKET_NAME, 'Key': key}

    # Add content disposition header to force download if requested
    if download:
        # Use provided filename or extract from key
        download_filename = filename or key.split('/')[-1]
        params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'

    url = s3.generate_presigned_url('get_object', Params=params, ExpiresIn=expiration)
    return url


def send_email_(email, variables, action):
    try:
        recipient_list = [email]
        template_variables = variables

        template = email_templates.get(action)
        subject = template.get('subject')
        html_message = template.get('html_message').format(**template_variables)

        send_mail(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )

    except Exception as e:
        logger.error(str(e))
        raise APIException(Error.RESPONSE_INVITATION_EMAIL_ERROR)


def snake_case(value):
    if isinstance(value, list):
        return [snake_case(v) for v in value]
    return value.lower().replace(' ', '_')


def unsnake_case(value):
    """Turns snake_case back into words with spaces and Title-Case."""
    if isinstance(value, list):
        return [unsnake_case(v) for v in value]
    return value.replace('_', ' ').title()


def str_to_bool(value):
    return str(value).lower() in ('true', '1', 't', 'y', 'yes')


def download_file_from_url(url, filename=None):
    """
    Downloads a file from a URL and returns a Django File object.
    Only allows PDF, JPG, PNG, and DOCX file types.

    Args:
        url (str): The URL to download the file from
        filename (str, optional): Custom filename to use. If None, extracts from URL.

    Returns:
        tuple: (Django File object, temp file path to be cleaned up)

    Raises:
        Exception: If download fails or file type is not allowed
    """
    try:
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)

            if not filename or '.' not in filename:
                response = requests.head(url)
                content_type = response.headers.get('Content-Type', '').lower()

                allowed_types = {
                    'application/pdf': '.pdf',
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/png': '.png',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                }

                if content_type not in allowed_types:
                    raise ValueError(f"File type '{content_type}' is not allowed. Only PDF, JPG, PNG, and DOCX are permitted.")

                extension = allowed_types[content_type]
                filename = f"document_{os.path.basename(tempfile.mktemp())}{extension}"
            else:
                ext = os.path.splitext(filename)[1].lower()
                allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx']

                if ext not in allowed_extensions:
                    return False, f"File extension '{ext}' is not allowed. Only PDF, JPG, PNG, and DOCX are permitted."
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        # Create a Django File object from the temp file
        django_file = File(open(temp_file_path, 'rb'), name=filename)

        return django_file, temp_file_path

    except Exception as e:
        logger.error(f"Error downloading file from URL {url}: {str(e)}")
        raise
