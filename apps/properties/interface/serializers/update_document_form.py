from rest_framework import serializers


class UpdateDocumentFormSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    data = serializers.JSONField()