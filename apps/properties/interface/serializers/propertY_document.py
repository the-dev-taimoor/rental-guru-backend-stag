from rest_framework import serializers

from apps.properties.infrastructure.models import PropertyDocument
from common.constants import Error
from common.utils import get_presigned_url


class PropertyDocumentSerializer(serializers.ModelSerializer):
    page_saved = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = PropertyDocument
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
        return rep

    def create(self, validated_data):
        page_saved = validated_data.pop('page_saved')
        documents = super().create(validated_data)
        if validated_data.get('unit'):
            obj = documents.unit
        else:
            obj = documents.property
        obj.page_saved = page_saved
        obj.save(update_fields=['page_saved'])
        return documents

    def validate(self, data):
        unit = data.get('unit')
        if PropertyDocument.objects.filter(property=data['property'], unit=unit, document_type=data['document_type']).exists():
            raise serializers.ValidationError(Error.DOCUMENT_TYPE_EXISTS)
        return data
