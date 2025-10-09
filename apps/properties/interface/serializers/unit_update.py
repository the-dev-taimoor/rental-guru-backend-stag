from rest_framework import serializers

from common.constants import Error
from common.utils import unsnake_case

from apps.properties.infrastructure.models import PropertyPhoto, Unit
from .property_photo import PropertyPhotoSerializer
from .unit import UnitSerializer

class UnitUpdateSerializer(UnitSerializer):
    existing_photos = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Unit
        fields = '__all__'

    def validate_type(self, value):
        """Validate unit type based on property type"""
        unit_instance = self.instance
        if unit_instance and unit_instance.property:
            property_type = unit_instance.property.property_type

            unit_choices = UnitSerializer.unit_type_by_choices.get(property_type, [])
            if unit_choices and value not in [choice[0] for choice in unit_choices]:
                raise serializers.ValidationError(
                    Error.INVALID_UNIT_TYPE.format(unsnake_case(property_type))
                )
        return value

    def to_representation(self, instance):
        """Include photos in the response"""
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(unit=instance.id)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation