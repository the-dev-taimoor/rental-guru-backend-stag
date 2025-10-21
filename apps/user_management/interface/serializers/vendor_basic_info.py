from rest_framework import serializers

from apps.user_management.infrastructure.models import Vendor


class VendorBasicInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor basic information tab"""

    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user_id.phone_number', read_only=True)
    email = serializers.CharField(source='user_id.email', read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'full_name',
            'phone_number',
            'email',
            'years_of_experience',
            'availability',
            'emergency_services',
            'languages',
            'insurance_coverage',
            'vendor_role',
        ]

    def get_full_name(self, obj):
        user = obj.user_id
        return f"{user.first_name} {user.last_name}".strip()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Convert boolean fields to user-friendly text
        rep['availability'] = 'Available' if instance.availability else 'Not Available'
        rep['emergency_services'] = 'Yes' if instance.emergency_services else 'No'
        rep['insurance_coverage'] = 'Yes' if instance.insurance_coverage else 'No'

        # Format years of experience
        if instance.years_of_experience:
            rep['years_of_experience'] = f"{instance.years_of_experience} years"

        return rep
