import re
import pandas as pd
from io import BytesIO
from collections import defaultdict

from django.db.models import Avg
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from common.utils import get_presigned_url, snake_case, str_to_bool, unsnake_case
from apps.user_authentication.infrastructure.models import PropertyOwner
from .exceptions import CustomValidationError
from .utils import xlsx_sheet_names, COLUMN_CONFIG
from apps.properties.infrastructure.models import (ListingInfo, Amenities, RentDetails, OwnerInfo, CostFee, CostFeesCategory, PropertyDocument,
                     PropertyPhoto, Property, CalendarSlot, Unit, PropertyAssignedAmenities)
from common.constants import Error, Success


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
        property_owner = data.get('property_owner')
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


class PropertyRetrieveSerializer(serializers.ModelSerializer):
    photos = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        exclude = ['property_owner', 'created_at', 'updated_at']
    
    def get_photos(self, obj):
        # Only get photos that don't belong to any unit (unit is null)
        photos = PropertyPhoto.objects.filter(property=obj.id, unit__isnull=True)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        return photos_data


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ['id', 'photo']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.photo.name:
            rep["photo"] = get_presigned_url(instance.photo.name)
        return rep


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


class ListingInfoUpdateSerializer(ListingInfoSerializer):
    existing_photos = serializers.JSONField(write_only=True, required=False)

    def validate(self, data):
        return data


class ListingInfoRetrieveSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False)

    class Meta:
        model = ListingInfo
        exclude = ['created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(property=instance.property, unit__isnull=True)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation


class RentDetailsSerializer(serializers.ModelSerializer):
    page_saved = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = RentDetails
        fields = '__all__'

    def create(self, validated_data):
        page_saved = validated_data.pop('page_saved')
        rental = super().create(validated_data)
        if validated_data.get('unit'):
            obj = rental.unit
        else:
            obj = rental.property
        obj.page_saved = page_saved
        obj.save(update_fields=['page_saved'])
        return rental

    def validate(self, data):
        unit = data.get('unit')

        is_update = self.instance is not None
        if not is_update:
            if RentDetails.objects.filter(property=data['property'], unit=unit).exists():
                raise serializers.ValidationError(Error.RENT_DETAILS_EXISTS)

        if data.get('assigned_tenant'):
            if data.get('promote_special_offer'):
                raise serializers.ValidationError(Error.OFFER_NOT_REQUIRED)
            else:
                if not (data.get('lease_start_date') and data.get('lease_end_date')):
                    raise serializers.ValidationError(
                        Error.TENANT_FIELDS_REQUIRED.format("'lease_start_date', 'lease_end_date'"))
        else:
            if data.get('promote_special_offer'):
                if not (data.get('offer_start_date') and data.get('offer_end_date') and data.get('offer_percentage')):
                    raise serializers.ValidationError(Error.OFFER_REQUIRED.format("'offer_start_date', 'offer_end_date', 'offer_percentage'"))
        return data


class RentDetailsRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = RentDetails
        exclude = ['created_at', 'updated_at']


class PropertyAmenitiesSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    unit_id = serializers.IntegerField(required=False)
    sub_amenities = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True
    )
    other_amenities = serializers.ListField(
        child=serializers.CharField(), allow_empty=True
    )
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


class PropertySummaryRetrieveSerializer:
    @staticmethod
    def get_amenities(property_id, unit_id):
        sub_amenities = PropertyAssignedAmenities.objects.filter(property=property_id, unit=unit_id).select_related(
            'sub_amenity')
        model = Property
        if unit_id:
            model = Unit
            instance_id = unit_id
        else:
            instance_id = property_id
        other_amenities = model.objects.filter(id=instance_id).values_list('other_amenities', flat=True)
        amenities_data = dict()
        for amenity in sub_amenities:
            a_name = amenity.sub_amenity.amenity
            if a_name not in amenities_data:
                amenities_data[a_name] = list()
            amenities_data[a_name].append({
                'id': amenity.sub_amenity.id,
                'name': amenity.sub_amenity.sub_amenity
            })
        amenities_data['other_amenities'] = list(other_amenities)
        return amenities_data

    @staticmethod
    def get_rental_details(property_id, unit_id):
        rental_details_instance = RentDetails.objects.filter(property=property_id, unit=unit_id).first()
        return RentDetailsRetrieveSerializer(rental_details_instance).data if rental_details_instance else None

    @staticmethod
    def get_listing_info(property_id):
        listing_info_instance = ListingInfo.objects.filter(property=property_id).first()
        return ListingInfoRetrieveSerializer(listing_info_instance).data if listing_info_instance else None

    @staticmethod
    def get_cost_fees(property_id, unit_id):
        cost_fee_data = []
        cost_category_instances = CostFeesCategory.objects.filter(property=property_id, unit=unit_id)
        for cost_fee in cost_category_instances:
            cost_fee_obj = {
                'category_name': cost_fee.category_name,
                'fees': [CostFeeRetrieveSerializer(f).data for f in CostFee.objects.filter(category=cost_fee.id)]
            }
            cost_fee_data.append(cost_fee_obj)
        return cost_fee_data

    @staticmethod
    def get_owners(property_id):
        owners_data = OwnerInfo.objects.filter(property=property_id)
        owners = list()
        for owner in owners_data:
            data = OwnerInfoRetrieveSerializer(owner).data
            try:
                get_user = get_user_model().objects.get(email=data.get('email'), is_active=True)
                data['username'] = get_user.first_name + ' ' + get_user.last_name
                data['phone_number'] = get_user.phone_number
                try:
                    profile = PropertyOwner.objects.filter(user_id=get_user.id).values_list('profile_image_path', flat=True).first()
                    if profile:
                        data['profile_image_path'] = get_presigned_url(profile)
                    else:
                        data['profile_image_path'] = None
                except PropertyOwner.DoesNotExist:
                    data['profile_image_path'] = None
            except get_user_model().DoesNotExist:
                data['username'] = None
                data['phone_number'] = None
                data['profile_image_path'] = None
            owners.append(data)
        return owners

    @staticmethod
    def get_documents(property_id, unit_id):
        document_instances = PropertyDocument.objects.filter(property=property_id, unit=unit_id)
        return [DocumentRetrieveSerializer(document).data for document in document_instances]


class CostFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFee
        fields = '__all__'

    def validate(self, data):
        if CostFee.objects.filter(**data).exists():
            raise serializers.ValidationError(Error.COST_FEE_EXISTS)
        return data


class CostFeeRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFee
        fields = ['id', 'fee_name', 'payment_frequency', 'fee_amount', 'fee_type', 'is_required', 'refundable_status', 'category']


class CostFeesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostFeesCategory
        fields = '__all__'


class OwnerInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = OwnerInfo
        fields = '__all__'


class OwnerInfoRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = OwnerInfo
        fields = ['id', 'email', 'percentage', 'emergency_person', 'emergency_contact', 'registered']


class PropertyDocumentSerializer(serializers.ModelSerializer):
    page_saved = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = PropertyDocument
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
        return rep

    def create(self, validated_data):
        page_saved = validated_data.pop('page_saved')
        documents = super().create(validated_data)
        if validated_data.get('unit'):
            obj = documents.unit
        else:
            obj = documents.property
        obj.page_saved = page_saved
        obj.save(update_fields=['page_saved'])
        return documents

    def validate(self, data):
        unit = data.get('unit')
        if PropertyDocument.objects.filter(property=data['property'], unit=unit,
                                           document_type=data['document_type']).exists():
            raise serializers.ValidationError(Error.DOCUMENT_TYPE_EXISTS)
        return data


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


class CalendarSlotListSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    month = serializers.IntegerField()
    year = serializers.IntegerField()


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


class UnitRetrieveSerializer(serializers.ModelSerializer):
    photo = PropertyPhotoSerializer(many=True, required=False)

    class Meta:
        model = Unit
        exclude = ['property', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        photos = PropertyPhoto.objects.filter(unit=instance.id)
        photos_data = PropertyPhotoSerializer(photos, many=True).data
        representation['photos'] = photos_data
        return representation


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


class UploadDocumentFormSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    page_saved = serializers.IntegerField()
    data = serializers.JSONField()
    documents = serializers.ListField(child=serializers.FileField(), required=False)


class UpdateDocumentFormSerializer(serializers.Serializer):
    property = serializers.IntegerField()
    unit = serializers.IntegerField(required=False)
    data = serializers.JSONField()


class DocumentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyDocument
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
        return rep

    def validate(self, data):
        property_wise_document_types = {
            'university_housing': ['lease_agreement', 'floor_plan', 'compliance_certificate', 'maintenance_log',
                                   'move_in_move_out_checklist', 'utility_bill_copy', 'inspection_report',
                                   'renovation_permit', 'other',],
            'others': ['lease_agreement', 'medical_clearance_form', 'care_plan_agreement', 'emergency_contact_form',
                       'medication_schedule', 'ada_compliance_certificate', 'fall_risk_assessment',
                       'service_log', 'insurance_verification', 'other']
        }
        unit = data.get('unit')
        property_type = data['property'].property_type
        if property_type == 'university_housing':
            if data['document_type'] not in property_wise_document_types.get('university_housing'):
                raise ValidationError(Error.DOCUMENT_TYPE_UNIVERSITY_HOUSING)
        else:
            if data['document_type'] not in property_wise_document_types.get('others'):
                raise ValidationError(Error.DOCUMENT_TYPE_OTHERS.format(property_type.replace('_', ' ').capitalize()))

        if data['document_type'] != 'other':
            if PropertyDocument.objects.filter(property=data['property'], unit=unit,
                                               document_type=data['document_type']).exists():
                raise ValidationError(Error.DOCUMENT_TYPE_EXISTS_V2.format(data['document_type'].replace('_', ' ').capitalize()))
        return data


class DocumentRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyDocument
        exclude = ['updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name, download=True)
        return rep


class BulkUnitImportSerializer(serializers.Serializer):
    property = serializers.IntegerField(required=True)
    file = serializers.FileField(required=True)

    def validate(self, attrs):
        if not attrs['file'].name.endswith('.xlsx'):
            raise CustomValidationError("File must be in XLSX format")

        property_instance = Property.objects.get(id=attrs['property'])
        property_type_ = property_instance.property_type
        key = 'others'
        if property_type_ == 'university_housing':
            xlsx_sheet_names_ = xlsx_sheet_names['university_housing']
            key = 'university_housing'
        else:
            xlsx_sheet_names_ = xlsx_sheet_names['others']

        try:
            file_data = attrs['file'].read()
            xls = pd.ExcelFile(BytesIO(file_data))

            # Validate sheet presence
            found_sheets = set(xls.sheet_names)
            required_sheets = set(xlsx_sheet_names_.keys())
            missing_sheets = required_sheets - found_sheets
            if missing_sheets:
                raise CustomValidationError(f"Missing sheets: {', '.join(missing_sheets)}")

            data = self.process_excel_data(xls, key)
            data['property'] = attrs['property']

            # Process all column transformations
            for section in COLUMN_CONFIG:
                if section in data:
                    self.process_section(data, section)

            return data

        except Exception as e:
            raise CustomValidationError(e)

    def process_excel_data(self, xls, key):
        """Process all sheets from Excel file into structured data"""
        if key == 'university_housing':
            number_col_uq = 'Room Number'
            sheet_name_uq = 'Room Details'
        else:
            number_col_uq = 'Unit Number'
            sheet_name_uq = 'Unit Info'
        all_data = {}

        for sheet_name, expected_columns in xlsx_sheet_names[key].items():
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                df.columns = df.columns.str.strip()

                # Validate columns
                missing_cols = set(expected_columns) - set(df.columns)
                if missing_cols:
                    raise CustomValidationError(f"Missing columns in {sheet_name}: {', '.join(missing_cols)}")

                # Process data
                sheet_data = defaultdict(list)
                for _, row in df.iterrows():
                    unit_key = snake_case(row[number_col_uq])
                    row_data = {expected_columns[col]: row[col] for col in df.columns if col in expected_columns}
                    sheet_data[unit_key].append(row_data)

                all_data[snake_case(sheet_name)] = dict(sheet_data)

                # Checking if photos are present for all units
                unit_df = pd.read_excel(xls, sheet_name=sheet_name_uq)
                unit_df.columns = unit_df.columns.str.strip()

                unit_numbers = unit_df[number_col_uq].tolist()
                unit_info_keys = set(unit_numbers)

                photo_df = pd.read_excel(xls, sheet_name='Photos')
                photo_df.columns = photo_df.columns.str.strip()
                photo_unit_numbers = set(photo_df[number_col_uq].tolist())

                units_without_photos = unit_info_keys - photo_unit_numbers
                if units_without_photos:
                    raise CustomValidationError(Error.PHOTO_REQUIRED_FOR_UNIT.format(', '.join(units_without_photos)))

            except Exception as e:
                raise CustomValidationError(f"Error in sheet {sheet_name}: {str(e)}")

        return all_data

    def process_section(self, data, section_name):
        """Generic method to process any section based on COLUMN_CONFIG"""
        config = COLUMN_CONFIG.get(section_name, {})
        if not config or section_name not in data:
            return

        for unit, items in data[section_name].items():
            if not items:
                continue

            # Iterate over each item in the list of the current unit
            for item in items:
                updates = {}
                for field, (target_field, target_value) in config["fields"].items():
                    if field in item and str_to_bool(item[field]):
                        updates[target_field] = target_value

                # Apply updates to the item if any
                if updates:
                    item.update(updates)

                # After updating, remove the original fields
                for field in config["fields"]:
                    if field in item:
                        del item[field]


class UserPropertyUnitSerializer(serializers.Serializer):
    """
    Serializer for user properties and units list API.
    Returns id, name, and type for each property/unit.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
