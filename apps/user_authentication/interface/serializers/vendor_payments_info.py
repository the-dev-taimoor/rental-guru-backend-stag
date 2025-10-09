from rest_framework import serializers

class VendorPaymentsInfoSerializer(serializers.Serializer):
    """Serializer for vendor payments information tab"""
    payment_method = serializers.CharField(default="Not Set")
    bank_account = serializers.CharField(default="Not Set")
    payment_history = serializers.ListField(default=list)