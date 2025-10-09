from rest_framework import serializers
from common.constants import Error

class LeaseManagementSerializer(serializers.Serializer):
    """
    Serializer for managing lease agreements (end or renew).
    """
    invitation_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(choices=['end', 'renew'], required=True)
    lease_start_date = serializers.DateField(required=False)
    lease_end_date = serializers.DateField(required=False)
    rent_amount = serializers.IntegerField(required=False)
    security_deposit = serializers.IntegerField(required=False)
    lease_agreement = serializers.FileField(required=False)


    def validate(self, attrs):
        action = attrs.get('action')
        lease_end_date = attrs.get('lease_end_date')
        lease_start_date = attrs.get('lease_start_date')
        rent_amount = attrs.get('rent_amount')
        lease_agreement = attrs.get('lease_agreement')

        if action == 'renew':
            if not lease_start_date:
                raise serializers.ValidationError(Error.LEASE_START_DATE_REQUIRED)
            if not lease_end_date:
                raise serializers.ValidationError(Error.LEASE_END_DATE_REQUIRED)
            if not rent_amount:
                raise serializers.ValidationError(Error.RENT_AMOUNT_REQUIRED)
            if not lease_agreement:
                raise serializers.ValidationError(Error.LEASE_AGREEMENT_REQUIRED)

        return attrs