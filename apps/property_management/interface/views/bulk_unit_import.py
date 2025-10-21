import os
from collections import defaultdict
from datetime import datetime

from django.db.models import F, Value
from django.db.models.functions import Lower, Replace
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from apps.property_management.infrastructure.models import (
    Amenities,
    CostFeesCategory,
    Property,
    PropertyAssignedAmenities,
    PropertyDocument,
    PropertyPhoto,
)
from apps.property_management.interface.serializers import (
    BulkUnitImportSerializer,
    CostFeeSerializer,
    RentDetailsSerializer,
    UnitSerializer,
)
from common.constants import Error, Success
from common.utils import CustomResponse, NotFound, custom_exception_handler, download_file_from_url, snake_case, unsnake_case


class BulkUnitImportAPIView(APIView):
    parser_classes = [MultiPartParser]
    serializer_class = BulkUnitImportSerializer

    def post(self, request):
        unit_errors = defaultdict(list)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            processed_data = serializer.validated_data
            property_id = processed_data.get("property")
            try:
                property_instance = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                raise NotFound(Error.PROPERTY_NOT_FOUND)

            if property_instance.property_type == 'university_housing':
                sheet_name_uq = 'room_details'
            else:
                sheet_name_uq = 'unit_info'

            total_units_allowed = int(
                property_instance.listing_info.number_of_units if property_instance.listing_info.number_of_units else 0
            )
            number_of_units_to_add = len(processed_data.get(sheet_name_uq).keys())
            existing_units_number = int(property_instance.unit_property.count() if property_instance.unit_property.count() else 0)
            if total_units_allowed < (number_of_units_to_add + existing_units_number):
                raise ValidationError(
                    Error.NUMBER_OF_UNITS_MISMATCH.format(total_units_allowed, existing_units_number, number_of_units_to_add)
                )

            total_units = len(processed_data.get(sheet_name_uq).keys())
            unit_success_count = 0
            for unit_key, obj in processed_data.get(sheet_name_uq).items():
                obj = obj[0]
                obj["property"] = property_instance.id
                serializer = UnitSerializer(data=obj)

                if not serializer.is_valid():
                    validation_error = ValidationError(serializer.errors)

                    error_response = custom_exception_handler(validation_error, {'view': self})

                    if error_response:
                        unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                    else:
                        unit_errors[unsnake_case(unit_key)].append(serializer.errors)
                    continue

                try:
                    unit_instance = UnitSerializer.csv_create(property_instance=property_instance, validated_data=obj)
                except ValidationError as e:
                    error_response = custom_exception_handler(e, {'view': self})

                    if error_response:
                        unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                    else:
                        unit_errors[unsnake_case(unit_key)].append(str(e))
                    continue
                unit_success_count += 1

                unit_instance.csv_upload = True
                unit_instance.save()

                photos = processed_data.get('photos')
                photos_detail = photos.get(unit_key)
                for photo in photos_detail:
                    photo_url = photo.get('photo')
                    if photo_url and isinstance(photo_url, str) and (photo_url.startswith('http://') or photo_url.startswith('https://')):
                        photo_url, temp_file_path = download_file_from_url(photo_url)
                        if not photo_url:
                            unit_errors[unsnake_case(unit_key)].append(temp_file_path)
                        else:
                            try:
                                PropertyPhoto.objects.create(property=property_instance, unit=unit_instance, photo=photo_url)
                            except ValidationError as e:
                                error_response = custom_exception_handler(e, {'view': self})
                                if error_response:
                                    unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                                else:
                                    unit_errors[unsnake_case(unit_key)].append(str(e))

                            if photo_url:
                                photo_url.close()
                                os.unlink(temp_file_path)

                rental_detail = processed_data.get('rent_details')
                unit_rental_detail = rental_detail.get(unit_key)
                detail = unit_rental_detail[0]
                detail['unit'] = unit_instance.id
                detail['property'] = property_instance.id
                detail['page_saved'] = 2
                serializer = RentDetailsSerializer(data=detail)
                if not serializer.is_valid():
                    validation_error = ValidationError(serializer.errors)

                    error_response = custom_exception_handler(validation_error, {'view': self})

                    if error_response:
                        unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                    else:
                        unit_errors[unsnake_case(unit_key)].append(serializer.errors)

                else:
                    try:
                        serializer.save()
                    except ValidationError as e:
                        error_response = custom_exception_handler(e, {'view': self})

                        if error_response:
                            unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                        else:
                            unit_errors[unsnake_case(unit_key)].append(str(e))

                amenities = processed_data.get('amenities')
                if amenities.get(unit_key):
                    amenities_ = amenities.get(unit_key)[0]['sub_amenities'].split(',')
                    amenities_list = snake_case([a.strip() for a in amenities_])
                    existing_amenities = (
                        Amenities.objects.annotate(normalized_sub=Lower(Replace(F("sub_amenity"), Value(" "), Value("_"))))
                        .filter(normalized_sub__in=amenities_list)
                        .values("id", "sub_amenity")
                    )

                    sub_amenities_ids = [item['id'] for item in existing_amenities]
                    sub_amenities_names = snake_case([item['sub_amenity'] for item in existing_amenities])

                    other_amenities = [amenity for amenity in amenities_list if amenity not in sub_amenities_names]

                    bulk_list = []
                    for sub_id in sub_amenities_ids:
                        sub_obj = get_object_or_404(Amenities, id=sub_id)

                        pa = PropertyAssignedAmenities(property=property_instance, sub_amenity=sub_obj, unit=unit_instance)
                        bulk_list.append(pa)

                    PropertyAssignedAmenities.objects.bulk_create(bulk_list)

                    unit_instance.other_amenities = other_amenities
                    unit_instance.page_saved = 3
                    unit_instance.save()
                else:
                    unit_errors[unsnake_case(unit_key)].append(
                        "Amenities were not found in the file. Edit the unit from Inactive units tab."
                    )

                cost_fee = processed_data.get('cost_fee')
                cost_fee_detail = cost_fee.get(unit_key)
                if cost_fee_detail:
                    for cost in cost_fee_detail:
                        cost_obj = dict()
                        cost_obj['property'] = property_instance
                        cost_obj['unit'] = unit_instance
                        cost_obj['category_name'] = cost.get('category_name')
                        category_obj = CostFeesCategory.objects.filter(
                            property=property_instance, unit=unit_instance, category_name=cost.get('category_name')
                        ).first()
                        if not category_obj:
                            category_obj = CostFeesCategory.objects.create(**cost_obj)
                        cost['category'] = category_obj.id
                        serializer = CostFeeSerializer(data=cost)
                        if not serializer.is_valid():
                            validation_error = ValidationError(serializer.errors)

                            error_response = custom_exception_handler(validation_error, {'view': self})

                            if error_response:
                                unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                            else:
                                unit_errors[unsnake_case(unit_key)].append(serializer.errors)

                        try:
                            serializer.save()
                        except ValidationError as e:
                            error_response = custom_exception_handler(e, {'view': self})

                            if error_response:
                                unit_errors[unsnake_case(unit_key)].append(error_response.data.get('error'))
                            else:
                                unit_errors[unsnake_case(unit_key)].append(str(e))
                    unit_instance.page_saved = 4
                    unit_instance.save()
                else:
                    unit_errors[unsnake_case(unit_key)].append("Cost fee was not found in the file. Edit the unit from Inactive units tab.")

                documents = processed_data.get('document')
                documents_detail = documents.get(unit_key)
                for document in documents_detail:
                    document_obj = dict()
                    document_obj['property'] = property_instance
                    document_obj['unit'] = unit_instance
                    document_obj['title'] = document.get('title')
                    document_obj['visibility'] = document.get('visibility')
                    document_obj['document_type'] = document.get('document_type')

                    # Handle document URL
                    document_url = document.get('documents')
                    if (
                        document_url
                        and isinstance(document_url, str)
                        and (document_url.startswith('http://') or document_url.startswith('https://'))
                    ):
                        try:
                            document_url, temp_file_path = download_file_from_url(document_url)
                            document_obj['document'] = document_url
                            PropertyDocument.objects.create(**document_obj)
                            if document_url:
                                document_url.close()
                                os.unlink(temp_file_path)
                        except Exception as e:
                            unit_errors[unsnake_case(unit_key)].append(f"Error downloading document: {str(e)}")

                unit_instance.page_saved = 5
                # if a unit has passed all the sections, then make it active
                unit_instance.published = True
                unit_instance.published_at = datetime.now()
                unit_instance.save()

            response_dict = {
                'csv_units_count': total_units,
                'units_created': unit_success_count,
                'units_failed': total_units - unit_success_count,
                'data': unit_errors,
            }

            if unit_success_count == total_units:
                return CustomResponse({'data': response_dict, 'message': Success.ALL_UNITS_CREATED}, status=status.HTTP_201_CREATED)
            else:
                unit_errors_ = f"Error in units; {', '.join(list(unit_errors.keys()))}."
                return CustomResponse(
                    {
                        'data': response_dict,
                        'message': Error.SOME_UNITS_NOT_CREATED.format(unit_success_count, total_units - unit_success_count),
                        'error': unit_errors_,
                    },
                    status=status.HTTP_201_CREATED,
                )

        else:
            return CustomResponse({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
