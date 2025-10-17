from rest_framework import serializers


class DummySerializer(serializers.Serializer):
    """A universal empty serializer for Swagger schema generation."""

    pass
