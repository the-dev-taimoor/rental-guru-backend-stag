import re
from rest_framework import serializers


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=20,
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    def validate_new_password(self, value):
        """
        Validate the new password based on the given criteria.
        """
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one uppercase letter.'})

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one lowercase letter.'})

        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one number.'})

        if not re.search(r'[@$!%*?&]', value):
            raise serializers.ValidationError({'password':'Password must contain at least one special character.'})

        return value

    def validate(self, data):
        """
        Ensure the new password and confirm password match.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data