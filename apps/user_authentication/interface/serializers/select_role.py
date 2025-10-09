from rest_framework import serializers

class SelectRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['property_owner', 'vendor', 'tenant'], required=True)