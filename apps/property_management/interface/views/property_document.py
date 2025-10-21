from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.property_management.infrastructure.models import PropertyDocument
from apps.property_management.interface.serializers import PropertyDocumentSerializer

from .general import GeneralViewSet


class PropertyDocumentViewSet(GeneralViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    parser_classes = [FormParser, MultiPartParser]
