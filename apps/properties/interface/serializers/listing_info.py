from rest_framework import serializers

from common.constants import Error
from apps.properties.infrastructure.models import ListingInfo, Property, PropertyPhoto
from .property_photo import PropertyPhotoSerializer

class ListingInfoSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False)
    page_saved = serializers.IntegerField(required=True, write_only=True)
    photos = PropertyPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = ListingInfo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.data.get('property'):
            try:
                property_id = request.data.get('property')
                property_instance = Property.objects.get(id=property_id)

                # Make occupancy_type required only for university_housing
                if property_instance.property_type == 'university_housing':
                    self.fields['occupancy_type'].required = True
            except Property.DoesNotExist:
                pass

    def create(self, validated_data):
        request = self.context.get('request')
        page_saved = validated_data.pop('page_saved')
        photos = request.FILES.getlist('photo') if request else []

        listing_info = super().create(validated_data)

        for photo in photos:
            PropertyPhoto.objects.create(property=listing_info.property, photo=photo)

        property_obj = listing_info.property
        property_obj.page_saved = page_saved
        property_obj.save(update_fields=['page_saved'])

        return listing_info

    def validate(self, data):
        """
        Custom validation to check if the photo field is present
        and if at least one photo is provided.
        """
        request = self.context.get('request')
        photos = request.FILES.getlist('photo') if request else []
        if not photos:
            raise serializers.ValidationError(Error.PHOTO_REQUIRED)
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(property=instance.property)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation