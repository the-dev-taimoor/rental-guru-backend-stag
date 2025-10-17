from rest_framework import serializers


class UploadDocumentFormSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    page_saved = serializers.IntegerField()
    data = serializers.JSONField()
    documents = serializers.ListField(child=serializers.FileField(), required=False)
