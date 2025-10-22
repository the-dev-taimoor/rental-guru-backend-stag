from rest_framework import serializers


class VendorJobInfoSerializer(serializers.Serializer):
    """Serializer for vendor jobs information tab"""

    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    jobs_completed = serializers.IntegerField(default=0)
    active_jobs = serializers.IntegerField(default=0)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, default=0)
