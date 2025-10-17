from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.properties.infrastructure.models import Property, PropertyDocument
from common.constants import Error
from common.utils import CustomResponse


class PropertyDocumentTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        unit_id = request.query_params.get('unit', None)
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)

        try:
            property_instance = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        property_type_ = property_instance.property_type
        if property_type_ == 'university_housing':
            document_types = PropertyDocument.DOCUMENT_TYPE_BY_PROPERTY_TYPE.get('university_housing')
        else:
            document_types = PropertyDocument.DOCUMENT_TYPE_BY_PROPERTY_TYPE.get('others')

        all_types = [choice[0] for choice in document_types]

        existing = set(PropertyDocument.objects.filter(property_id=property_id, unit_id=unit_id).values_list('document_type', flat=True))

        missing = [t for t in all_types if t not in existing and t != 'other']
        missing.append('other')

        return CustomResponse({"data": missing}, status=status.HTTP_200_OK)
