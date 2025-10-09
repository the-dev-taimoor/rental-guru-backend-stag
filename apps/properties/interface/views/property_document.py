from .general import GeneralViewSet

from apps.properties.infrastructure.models import PropertyDocument
from apps.properties.interface.serializers import PropertyDocumentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

class PropertyDocumentViewSet(GeneralViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    parser_classes = [FormParser, MultiPartParser]