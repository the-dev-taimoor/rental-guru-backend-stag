from rest_framework import serializers

from apps.properties.infrastructure.models import CalendarSlot

class CalendarSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSlot
        fields = ['id', 'date', 'status', 'property', 'unit', 'reason']

    def validate(self, data):
        unit = data.get('unit')
        property_ = data.get('property')
        date = data.get('date')

        existing_slot = CalendarSlot.objects.filter(property=property_, unit=unit, date=date).first()

        if existing_slot:
            existing_slot.delete()

        return data