from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import NotFound


class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    is_superuser = serializers.BooleanField(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        is_superuser = attrs.get("is_superuser", False)

        user = get_user_model().objects.filter(email=email, email_verified=True, is_superuser=is_superuser).first()
        if user is None:
            if is_superuser:
                raise NotFound("Not an admin user.")
            raise NotFound("User not found.")
        if not user.email_verified:
            raise serializers.ValidationError({"email": "Email not verified."})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Incorrect password."})
        return user
