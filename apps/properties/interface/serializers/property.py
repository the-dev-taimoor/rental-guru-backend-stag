import re
from rest_framework import serializers
from django.db.models import Avg

from common.constants import Error
from apps.properties.infrastructure.models import ListingInfo, RentDetails, PropertyPhoto, Property
from .property_photo import PropertyPhotoSerializer

class PropertySerializer(serializers.ModelSerializer):
    property_owner = serializers.PrimaryKeyRelatedField(required=False, read_only=True)
    rent = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    number_of_units = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['property_owner'] = user
        self._check_unique_property(validated_data)
        if validated_data['property_type'] != 'single_family_home':
            validated_data['status'] = ''
        property_instance = super().create(validated_data)
        return property_instance

    def _check_unique_property(self, data):
        """
        Check if a property with the same street address already exists.
        If it does, raise a ValidationError with a custom error message.
        """
        # property_owner = data.get('property_owner')
        street_address = data.get('street_address')
        property_type = data.get('property_type')

        if Property.objects.filter(property_type=property_type, street_address=street_address).exists():
            raise serializers.ValidationError({"detail": Error.OWNER_AND_PROPERTY_EXISTS})

    def validate_zip_code(self, value):
        if value in (None, ''):
            return value

        if not re.fullmatch(r'\d+', value):
            raise serializers.ValidationError(Error.NUMERIC_ZIP_CODE)
        return value

    def get_rent(self, obj):
        if obj.property_type == 'single_family_home':
            rental_details = RentDetails.objects.filter(property=obj.id).first()
            if rental_details:
                return rental_details.rent
        else:
            avg_rent = RentDetails.objects.filter(property=obj.id).aggregate(avg_rent=Avg('rent'))['avg_rent']
            return round(avg_rent, 2) if avg_rent is not None else None
        return None

    def get_photos(self, obj):
        photos = PropertyPhoto.objects.filter(property=obj.id, unit__isnull=True)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        return photos_data

    def get_number_of_units(self, obj):
        listing_info = ListingInfo.objects.filter(property=obj.id).first()
        if listing_info:
            return listing_info.number_of_units
        return None