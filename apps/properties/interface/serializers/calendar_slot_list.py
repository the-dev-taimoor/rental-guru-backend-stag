from rest_framework import serializers

class CalendarSlotListSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    month = serializers.IntegerField()
    year = serializers.IntegerField()