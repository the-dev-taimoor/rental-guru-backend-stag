from rest_framework import serializers

from apps.user_authentication.infrastructure.models import TenantInvitation


class TenantInvitationSerializer(serializers.ModelSerializer):
    lease_agreement = serializers.FileField(required=True)

    class Meta:
        model = TenantInvitation
        fields = [
            'first_name',
            'last_name',
            'email',
            'assignment_type',
            'assignment_id',
            'tenant_type',
            'lease_amount',
            'security_deposit',
            'lease_start_date',
            'lease_end_date',
            'lease_agreement',
        ]

    def validate(self, attrs):
        assignment_type = attrs.get('assignment_type')
        assignment_id = attrs.get('assignment_id')

        if assignment_type == 'property':
            from apps.properties.infrastructure.models import Property

            try:
                Property.objects.get(id=assignment_id)
            except Property.DoesNotExist:
                raise serializers.ValidationError("Property with this ID does not exist.")
        elif assignment_type == 'unit':
            from apps.properties.infrastructure.models import Unit

            try:
                Unit.objects.get(id=assignment_id)
            except Unit.DoesNotExist:
                raise serializers.ValidationError("Unit with this ID does not exist.")
        else:
            raise serializers.ValidationError("assignment_type must be either 'unit' or 'property'.")

        return attrs
