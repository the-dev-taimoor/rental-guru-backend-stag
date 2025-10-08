from django.utils.encoding import force_str
from rest_framework.exceptions import ErrorDetail
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.exceptions import ValidationError


class CustomValidationError(ValidationError):

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        # For validation failures, we may collect many errors together,
        # so the details should always be coerced to a list if not already.
        if isinstance(detail, tuple):
            detail = list(detail)
        if isinstance(detail, ValidationError):
            # Handle ValidationError more safely
            if hasattr(detail, 'detail'):
                # If it has a detail attribute (DRF ValidationError), use that
                detail = detail.detail
            elif hasattr(detail, 'args') and detail.args:
                # If it has args (standard Python exceptions), use the first arg
                detail = detail.args[0]
            else:
                # Fallback to string representation
                detail = str(detail)
        elif not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = custom_get_error_details(detail, code)


def custom_get_error_details(data, default_code=None):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, (list, tuple)):
        ret = [
            custom_get_error_details(item, default_code) for item in data
        ]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, dict):
        ret = {
            key: custom_get_error_details(value, default_code)
            for key, value in data.items()
        }
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret

    text = force_str(data)
    return text