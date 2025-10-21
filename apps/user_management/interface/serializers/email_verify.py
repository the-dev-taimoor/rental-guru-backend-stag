from rest_framework import serializers


class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
