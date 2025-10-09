from rest_framework import serializers

class OTPEnableSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.BooleanField()