from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=True)

    invitation_id = serializers.IntegerField(required=False)
    invitation_role = serializers.CharField(required=False)

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
            'phone_number',
            'otp_enable',
            'email_verified',
            'page_saved',
            'invitation_id',
            'invitation_role',
        ]
        extra_kwargs = {'password': {'write_only': True}, 'confirm_password': {'write_only': True}}

    # Validation logic is okay inside serializers
    def validate(self, data):
        """
        Validate that the password and confirm password match.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = get_user_model().objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data['phone_number'],
        )

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.username = validated_data['email']
        user.save()
        return user
