from rest_framework import serializers

from apps.properties.infrastructure.models import Amenities


class PropertyAmenitiesSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    unit_id = serializers.IntegerField(required=False)
    sub_amenities = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    other_amenities = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    page_saved = serializers.IntegerField(required=True, write_only=True)

    def validate(self, data):
        """
        Ensure all sub_amenities IDs are valid and belong to existing SubAmenity objects.
        """
        sub_ids = data.get('sub_amenities', [])
        existing_subs = Amenities.objects.filter(id__in=sub_ids)
        if len(existing_subs) != len(sub_ids):
            invalid_ids = set(sub_ids) - set(existing_subs.values_list('id', flat=True))
            raise serializers.ValidationError(f"Invalid sub_amenity IDs: {invalid_ids}")
        return data
