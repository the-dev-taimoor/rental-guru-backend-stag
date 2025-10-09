from rest_framework import serializers

class OTPCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=['SIGNUP', 'FORGOT-PASSWORD', 'SEND-OTP'], required=True, error_messages={
        'invalid_choice': 'It must be either "SIGNUP", "FORGOT-PASSWORD" or "SEND-OTP".'
    })