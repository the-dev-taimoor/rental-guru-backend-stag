from rest_framework import serializers
from rest_framework.exceptions import NotFound

from common.constants import Error
from common.utils import snake_case
from apps.properties.infrastructure.models import RentDetails, Unit, Property, PropertyPhoto

from .property_photo import PropertyPhotoSerializer

class UnitSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False)
    rent = serializers.SerializerMethodField() # for list of units API
    photos = serializers.SerializerMethodField() # for list of units API
    tenants = serializers.SerializerMethodField() # for list of units API
    unit_type_by_choices = {
        'multi_family': [
            ('unit_a', "Unit A"),
            ('unit_b', "Unit B"),
            ('upper_floor', "Upper Floor"),
            ('lower_floor', "Lower Floor"),
            ('rear_unit', "Rear Unit"),
            ('front_unit', "Front Unit"),
        ],
        'apartment_unit': [
            ('1bhk', "1BHK"),
            ('2bhk', "2BHK"),
            ('studio', "Studio"),
        ],
        'student_housing': [
            ('private', "Private"),
            ('shared', "Shared"),
            ('required', "Required"),
        ],
        'senior_living': [
            ('studio', "Studio"),
            ('1_bedroom', "1 Bedroom"),
            ('2_bedroom', "2 Bedroom"),
            ('companion_suite', "Companion Suite"),
            ('accessible_unit', "Accessible Unit"),
            ('memory_care_unit', "Memory Care Unit"),
            ('private_room', "Private Room"),
            ('shared_room', "Shared Room"),
        ],
        'university_housing': [
            ('private', "Private"),
            ('shared', "Shared"),
            ('double_occupancy', "Double Occupancy"),
            ('triple_occupancy', "Triple Occupancy"),
            ('studio', "Studio"),
        ],
    }

    class Meta:
        model = Unit
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        unit_type = validated_data.get('type')
        property_id = request.data['property']
        try:
            property_instance = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)
        property_type_ = property_instance.property_type

        photos = request.FILES.getlist('photo') if request else []
        if not photos:
            raise serializers.ValidationError(Error.PHOTO_REQUIRED)

        unit_choices = self.unit_type_by_choices.get(property_type_, [])
        if unit_type not in [choice[0] for choice in unit_choices]:
            raise serializers.ValidationError(Error.INVALID_UNIT_TYPE.format(property_type_))

        self.validate_fields(validated_data, property_type_)

        unit_info = super().create(validated_data)

        for photo in photos:
            PropertyPhoto.objects.create(property=unit_info.property, unit=unit_info, photo=photo)

        return unit_info

    def validate_fields(self, data, property_type_):
        if property_type_ == 'university_housing':
            if 'desks' not in data:
                raise serializers.ValidationError(Error.DESKS_REQUIRED)
            if 'beds' not in data:
                raise serializers.ValidationError(Error.BEDS_REQUIRED)
        else:
            if 'bedrooms' not in data:
                raise serializers.ValidationError(Error.BEDROOMS_REQUIRED)
            if 'bathrooms' not in data:
                raise serializers.ValidationError(Error.BATHROOMS_REQUIRED)

    @staticmethod
    def csv_create(property_instance, validated_data):
        """
        Create a Unit instance after validating property existence and unit type.
        """
        unit_type = snake_case(validated_data.get('type'))
        validated_data['type'] = unit_type
        property_type_ = property_instance.property_type
        unit_choices = UnitSerializer.unit_type_by_choices.get(property_type_, [])

        if unit_type not in [choice[0] for choice in unit_choices]:
            raise serializers.ValidationError(Error.INVALID_UNIT_TYPE.format(property_type_))

        model_fields = [field.name for field in Unit._meta.get_fields()]
        unit_data = {key: validated_data[key] for key in validated_data if key in model_fields}
        unit_data['property'] = property_instance
        unit_instance = Unit.objects.create(**unit_data)
        return unit_instance

    def get_rent(self, obj):
        rental_details = RentDetails.objects.filter(unit=obj.id).first()
        if rental_details:
            return rental_details.rent
        return None

    def get_photos(self, obj):
        photos = obj.unit_photos.all()
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        return photos_data

    def get_tenants(self, obj):
        rental_details = RentDetails.objects.filter(unit=obj.id).first()
        if rental_details:
            return rental_details.assigned_tenant
        return None