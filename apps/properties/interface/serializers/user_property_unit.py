from rest_framework import serializers

class UserPropertyUnitSerializer(serializers.Serializer):
    """
    Serializer for user properties and units list API.
    Returns id, name, and type for each property/unit.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
