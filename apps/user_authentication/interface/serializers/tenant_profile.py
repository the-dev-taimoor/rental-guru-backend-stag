from rest_framework import serializers

from apps.user_authentication.infrastructure.models import Tenant


class TenantProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenant
        fields = '__all__'

    def validate_investment_preferences(self, value):
        """
        Validate that investment_preferences contains only valid choices
        """
        if value is None:
            return value

        if not isinstance(value, list):
            raise serializers.ValidationError("Investment preferences must be a list.")

        valid_choices = [choice[0] for choice in Tenant.INVESTMENT_PREFERENCES_CHOICES]

        for preference in value:
            if preference not in valid_choices:
                raise serializers.ValidationError(
                    f"'{preference}' is not a valid investment preference. " f"Valid choices are: {', '.join(valid_choices)}"
                )

        return list(dict.fromkeys(value))
