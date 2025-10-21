from rest_framework import serializers

from apps.property_management.infrastructure.models import PropertyDocument
from common.utils import get_presigned_url


class DocumentRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyDocument
        exclude = ['updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name, download=True)
        return rep
