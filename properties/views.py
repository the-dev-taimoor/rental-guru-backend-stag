import os
import json
from collections import defaultdict
from datetime import datetime, timedelta
from django.db import IntegrityError
from django.db.models import Q, F, Value
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.functions import Lower, Replace

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from rental_guru.utils import CustomResponse, send_email_, custom_exception_handler, snake_case, unsnake_case, download_file_from_url
from rental_guru.constants import Success, Error
from .models import (Property, ListingInfo, RentDetails, Amenities, PropertyTypeAndAmenity,
                     PropertyAssignedAmenities, CostFeesCategory, OwnerInfo, PropertyDocument, CalendarSlot,
                     Unit, Invitation, CostFee, PropertyPhoto)
from .serializers import (PropertySerializer, ListingInfoSerializer, RentDetailsSerializer, PropertyAmenitiesSerializer,
                          CostFeesCategorySerializer, OwnerInfoSerializer, PropertyDocumentSerializer,
                          CalendarSlotSerializer, UploadDocumentFormSerializer, DocumentCreateSerializer,
                          UnitSerializer, CalendarSlotListSerializer, CostFeeSerializer, DocumentRetrieveSerializer,
                          CostFeeRetrieveSerializer, OwnerInfoRetrieveSerializer, UpdateDocumentFormSerializer,
                          PropertyRetrieveSerializer, UnitRetrieveSerializer, BulkUnitImportSerializer,
                          ListingInfoUpdateSerializer, UnitUpdateSerializer, UserPropertyUnitSerializer)
from .serializers import PropertySummaryRetrieveSerializer
from .filters import PropertyFilter, UnitFilter, DocumentFilter, CustomSearchFilter
from .utils import cost_fee_options
from properties.filters import CustomSearchFilter
from user_authentication.permissions import IsKYCApproved, IsPropertyOwner, IsUnitOwner
from user_authentication.pagination import PropertiesPagination, DocumentsPagination, UnitsPagination, UserPropertiesAndUnitsPagination


class GeneralViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_200_OK)


class PropertyViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    pagination_class = PropertiesPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PropertyFilter
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'], url_path='publish', permission_classes=[IsAuthenticated, IsKYCApproved, IsPropertyOwner])
    def publish(self, request, pk=None):
        try:
            property = self.get_object()
        except Property.DoesNotExist:
            return CustomResponse({"error": Error.PROPERTY_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        published = request.data.get('published', None)
        if published is None:
            return CustomResponse({"error": Error.PUBLISHED_FIELD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        property.published = published
        property.published_at = datetime.now() if published else None
        property.save()

        serializer = self.get_serializer(property)

        return CustomResponse({"message": Success.PROPERTY_PUBLISHED_STATUS, "data": serializer.data},
                        status=status.HTTP_200_OK)

    def get_queryset(self):
        return self.queryset.filter(property_owner=self.request.user)

    def get_object(self):
        try:
            return Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)


class TopListingsViewSet(GeneralViewSet):
    queryset = Property.objects.filter(published=True)
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.order_by('-created_at')[:8]


class PropertyRetrieveViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        property_instance = self.get_object()
        all_data = self.get_combined_data(property_instance, property_instance.id, unit_instance=None, unit_id=None)
        all_data['units'] = list()
        unit_instances = Unit.objects.filter(property=property_instance.id)
        for unit_instance in unit_instances:
            unit_data = self.get_combined_data(property_instance, property_instance.id, unit_instance, unit_instance.id)
            all_data['units'].append(unit_data)
        return CustomResponse({'data': all_data})

    def get_combined_data(self, property_instance, property_id, unit_instance, unit_id):
        details_serializer = PropertyRetrieveSerializer(property_instance)
        unit_data = {
            'rental_details': PropertySummaryRetrieveSerializer.get_rental_details(property_id, unit_id),
            'amenities': PropertySummaryRetrieveSerializer.get_amenities(property_id, unit_id=unit_id),
            'cost_fees': PropertySummaryRetrieveSerializer.get_cost_fees(property_id, unit_id),
            'documents': PropertySummaryRetrieveSerializer.get_documents(property_id, unit_id)
        }
        if not unit_id:
            property_data = {
                'detail': details_serializer.data,
                'listing_info': PropertySummaryRetrieveSerializer.get_listing_info(property_id),
                'owners': PropertySummaryRetrieveSerializer.get_owners(property_id),
            }
            unit_data.update(property_data)
        else:
            unit_details_serializer = UnitRetrieveSerializer(unit_instance)
            property_data = {
                'detail': unit_details_serializer.data
            }
            unit_data.update(property_data)

        return unit_data


class UnitSummaryViewSet(GeneralViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        unit_instance = self.get_object()
        property_instance = unit_instance.property
        all_data = self.get_combined_data(property_instance, property_instance.id, unit_instance, unit_instance.id)
        return CustomResponse({'data': all_data})

    def get_combined_data(self, property_instance, property_id, unit_instance, unit_id):
        details_serializer = UnitRetrieveSerializer(unit_instance)
        unit_data = {
            'detail': details_serializer.data,
            'rental_details': PropertySummaryRetrieveSerializer.get_rental_details(property_id, unit_id),
            'amenities': PropertySummaryRetrieveSerializer.get_amenities(property_id, unit_id=unit_id),
            'cost_fees': PropertySummaryRetrieveSerializer.get_cost_fees(property_id, unit_id),
            'documents': PropertySummaryRetrieveSerializer.get_documents(property_id, unit_id)
        }
        return unit_data


class PropertyMetricsViewSet(GeneralViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        property_instance = self.get_object()
        all_data = dict()
        all_data['rental_income'] = '-'
        all_data['occupancy_rate'] = '-'
        all_data['avg_lease_term'] = '-'
        all_data['avg_tenant_rating'] = '-'
        return CustomResponse({'data': all_data, 'message': Success.PROPERTY_METRICS})


class ListingInfoViewSet(GeneralViewSet):
    queryset = ListingInfo.objects.all()
    serializer_class = ListingInfoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_listing_object(self):
        try:
            property_instance = Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)
        try:
            return ListingInfo.objects.get(property_id=property_instance.id)
        except ListingInfo.DoesNotExist:
            raise NotFound(Error.LISTING_INFO_NOT_FOUND)

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_listing_object()
        serializer = ListingInfoUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        existing_photos = serializer.validated_data.pop('existing_photos', [])
        # delete every photo _not_ in the keep-list
        PropertyPhoto.objects.filter(property=serializer.instance.property).exclude(id__in=existing_photos).delete()
        # add new photos
        photos = request.FILES.getlist('photo') if request else []
        for photo in photos:
            PropertyPhoto.objects.create(property=serializer.instance.property, photo=photo)
        self.perform_update(serializer)
        return CustomResponse({'data': serializer.data, 'message': Success.LISTING_INFO_UPDATED})


class RentalDetailViewSet(GeneralViewSet):
    queryset = RentDetails.objects.all()
    serializer_class = RentDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_rental_object(self):
        try:
            property_instance = Property.objects.get(id=self.kwargs['pk'])
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)
        unit_id = self.kwargs.get('unit', None)
        try:
            return RentDetails.objects.get(property_id=property_instance.id, unit_id=unit_id)
        except RentDetails.DoesNotExist:
            raise NotFound(Error.RENTAL_DETAIL_NOT_FOUND.format('unit' if unit_id else 'property'))

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        request_data = request.data
        self.kwargs['unit'] = request_data.get('unit')
        partial = kwargs.pop('partial', False)
        instance = self.get_rental_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return CustomResponse({'data': serializer.data, 'message': Success.RENTAL_INFO_UPDATED})


class AmenitiesView(GeneralViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PropertyTypeAndAmenity.objects.all()
    serializer_class = PropertyAmenitiesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property_type']

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        page_saved = serializer.validated_data.get('page_saved')
        property_id = serializer.validated_data['property_id']
        sub_amenities_ids = serializer.validated_data.get('sub_amenities', [])
        other_amenities = serializer.validated_data.get('other_amenities', [])
        unit_id = serializer.validated_data.get('unit_id', None)

        property_obj = get_object_or_404(Property, id=property_id)

        if unit_id:
            unit_obj = get_object_or_404(Unit, id=unit_id)
        else:
            unit_obj = None

        PropertyAssignedAmenities.objects.filter(property=property_obj, unit=unit_obj).delete()

        bulk_list = []
        for sub_id in sub_amenities_ids:
            sub_obj = get_object_or_404(Amenities, id=sub_id)

            pa = PropertyAssignedAmenities(
                property=property_obj,
                sub_amenity=sub_obj,
                unit=unit_obj
            )
            bulk_list.append(pa)

        PropertyAssignedAmenities.objects.bulk_create(bulk_list)

        unit_id = None
        if unit_obj:
            obj = unit_obj
            unit_id = unit_obj.id
        else:
            obj = property_obj

        obj.other_amenities = other_amenities
        obj.page_saved = page_saved
        obj.save(update_fields=['other_amenities', 'page_saved'])

        amenities_data = PropertySummaryRetrieveSerializer.get_amenities(property_id=property_obj.id, unit_id=unit_id)

        return CustomResponse(
            {
                'data': amenities_data,
                'message': Success.AMENITIES_UPDATED
            },
            status=status.HTTP_200_OK
        )

    def list(self, request, *args, **kwargs):
        filtered_queryset = self.filter_queryset(self.get_queryset())
        amenity_ids = filtered_queryset.values_list('sub_amenities', flat=True)
        amenities = Amenities.objects.filter(id__in=amenity_ids)
        amenities_dict = {}
        for item in amenities:
            if item.amenity not in amenities_dict:
                amenities_dict[item.amenity] = []

            amenities_dict[item.amenity].append({
                'id': item.id,
                'sub_amenity': item.sub_amenity
            })

        result = [
            {'amenity': key, 'sub_amenities': value}
            for key, value in amenities_dict.items()
        ]

        return CustomResponse({'data': result, 'message': Success.AMENITIES_AND_SUB_AMENITIES},
                        status=status.HTTP_200_OK)


class CostFeeViewSet(APIView):
    permission_classes = [IsAuthenticated]
    queryset = CostFeesCategory.objects.all()
    serializer_class = CostFeesCategorySerializer

    def post(self, request):
        updated_call = False
        data = request.data.copy()
        unit = data.get('unit')
        cost_fees = data.pop('cost_fees')
        property_ = data.pop('property')
        page_saved = data.get('page_saved')
        if not page_saved:
            raise ValidationError(Error.PAGE_SAVED_REQUIRED)

        self.check_fee_id_exists_update_case(cost_fees, property_, unit)
        self.check_fee_exists_create_case(cost_fees, property_, unit)

        all_data = list()

        for cost_fee in cost_fees:
            category_data = dict()
            parent_data = dict()
            category_name = cost_fee.get('category_name')
            parent_data['unit'] = unit
            parent_data['property'] = property_
            parent_data['category_name'] = category_name

            existing_category = CostFeesCategory.objects.filter(property=property_, unit=unit, category_name=category_name).first()

            if existing_category:
                category = existing_category
            else:
                serializer = self.serializer_class(data=parent_data)
                serializer.is_valid(raise_exception=True)
                category = CostFeesCategory.objects.create(**serializer.validated_data)

            category_data['category_name'] = category_name

            fees_data = list()
            fees = cost_fee.get('fees')

            for fee in fees:
                fee_id = fee.get('id')
                if fee_id:
                    self.perform_custom_update(fee_id, fee, fees_data)
                    updated_call = True
                else:
                    self.perform_custom_create(category, fee, fees_data)

            category_data['fees'] = fees_data
            all_data.append(category_data)

        try:
            property_obj = Property.objects.get(id=property_)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        if not updated_call:
            property_obj.page_saved = page_saved
            property_obj.save(update_fields=['page_saved'])

        return CustomResponse({'message': Success.COST_FEE_ADDED, 'data': all_data})

    def check_fee_id_exists_update_case(self, cost_fees, property_, unit):
        existing_fees_ids = [f.get('id') for c in cost_fees for f in c.get('fees') if f.get('id')]
        existing_fees = CostFee.objects.filter(id__in=existing_fees_ids, category__property=property_, category__unit=unit)

        # Check if all IDs from payload exist in database
        db_fee_ids = set(existing_fees.values_list('id', flat=True))
        missing_ids = set(existing_fees_ids) - db_fee_ids

        if missing_ids:
            raise ValidationError(Error.COST_FEE_ID_NOT_FOUND.format(', '.join(map(str, missing_ids))))

    def check_fee_exists_create_case(self, cost_fees, property_id, unit_id):
        for cost_fee in cost_fees:
            category_name = cost_fee.get('category_name')
            fees = cost_fee.get('fees')
            for fee in fees:
                if not fee.get('id'):
                    if CostFee.objects.filter(category__property=property_id,
                                              category__unit=unit_id,
                                              category__category_name=category_name,
                                              fee_name=fee.get('fee_name')).exists():
                        raise ValidationError(Error.COST_FEE_NAME_EXISTS.format(fee.get('fee_name')))

    def perform_custom_update(self, fee_id, fee, fees_data):
        try:
            existing_fee = CostFee.objects.get(id=fee_id)
        except CostFee.DoesNotExist:
            raise NotFound(Error.COST_FEE_ID_NOT_FOUND.format(fee_id))

        for field, value in fee.items():
            if field not in ['id', 'category']:
                setattr(existing_fee, field, value)
        existing_fee.save()
        fee_serializer = CostFeeRetrieveSerializer(existing_fee)
        fees_data.append(fee_serializer.data)

    def perform_custom_create(self, category, fee, fees_data):
        fee['category'] = category.id
        fee_serializer = CostFeeSerializer(data=fee)
        fee_serializer.is_valid(raise_exception=True)
        new_fee_instance = CostFee.objects.create(**fee_serializer.validated_data)
        
        response_serializer = CostFeeRetrieveSerializer(new_fee_instance)
        fees_data.append(response_serializer.data)


class PropertyOwnerViewSet(APIView):
    permission_classes = [IsAuthenticated]
    queryset = OwnerInfo.objects.all()
    serializer_class = OwnerInfoSerializer

    def post(self, request):
        updated_call = False
        all_data = list()
        data = request.data.copy()
        owner = request.user
        owners = data.pop('owners')
        property = data.pop('property')
        page_saved = data.pop('page_saved')
        registered_users = list()
        unregistered_users = list()
        messages = []

        try:
            property_obj = Property.objects.get(id=property)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        self.check_owners_exists_create_case(owners, property)
        self.check_owners_exists_update_case(owners)

        for own in owners:
            if own.get('id'):
                updated_call = True
                self.update_owner(own, all_data, messages)
            else:
                if get_user_model().objects.filter(email=own.get('email'), is_active=True):
                    registered_users.append(own)
                else:
                    unregistered_users.append(own)

        for registered_user in registered_users:
            success = self.add_owner(registered_user, messages, owner.id, property, all_data, registered=True)
            if success:
                receiver_email = registered_user.get('email')
                variables = {'SETUP_LINK': settings.SITE_DOMAIN + '/signup'}
                send_email_(receiver_email, variables, 'INVITE-EXISTING-OWNER')
                try:
                    Invitation.objects.create(sender=owner, receiver_email=receiver_email, role='property_owner')
                except IntegrityError:
                    messages.append(Error.INVITATION_ALREADY_SENT.format(registered_user.get('email')))
                    continue

        for unregistered_user in unregistered_users:
            success = self.add_owner(unregistered_user, messages, owner.id, property, all_data, registered=False)

            if success:
                receiver_email = unregistered_user.get('email')
                variables = {'SETUP_LINK': settings.SITE_DOMAIN + '/signup'}
                send_email_(receiver_email, variables, 'INVITE-OWNER')
                try:
                    Invitation.objects.create(sender=owner, receiver_email=receiver_email, role='property_owner')
                except IntegrityError:
                    messages.append(Error.INVITATION_ALREADY_SENT.format(unregistered_user.get('email')))
                    continue

        if not updated_call:
            property_obj.page_saved = page_saved
            property_obj.save(update_fields=['page_saved'])

        if messages:
            message = ', '.join(messages)
            return CustomResponse({'message': message, 'data': all_data}, status=200)

        return CustomResponse({'message': Success.OWNERS_ADDED, 'data': all_data})

    def add_owner(self, user_, messages, owner_id, property_id, all_data, registered):
        user_['owner'] = owner_id
        user_['property'] = property_id
        user_['registered'] = registered
        if self.queryset.filter(owner=owner_id, property=property_id, email=user_.get('email')).exists():
            messages.append(Error.EMAIL_ALREADY_ASSIGNED.format(user_.get('email')))
            return False

        serializer = self.serializer_class(data=user_)

        if serializer.is_valid():
            try:
                new_owner_instance = OwnerInfo.objects.create(**serializer.validated_data)
                serializer = OwnerInfoRetrieveSerializer(new_owner_instance)
                all_data.append(serializer.data)
            except IntegrityError:
                messages.append(Error.EMAIL_ALREADY_ASSIGNED.format(user_.get('email')))
                return False
        return True

    def check_owners_exists_create_case(self, owners, property_id):
        for own in owners:
            if not own.get('id'):
                if OwnerInfo.objects.filter(email=own.get('email'), property=property_id).exists():
                    raise ValidationError(Error.EMAIL_ALREADY_ASSIGNED.format(own.get('email')))

    def check_owners_exists_update_case(self, owners):
        existing_owners_ids = [o.get('id') for o in owners if o.get('id')]
        existing_owners = OwnerInfo.objects.filter(id__in=existing_owners_ids)

        # Check if all IDs from payload exist in database
        db_owner_ids = set(existing_owners.values_list('id', flat=True))
        missing_ids = set(existing_owners_ids) - db_owner_ids

        if missing_ids:
            raise ValidationError(Error.OWNER_ID_NOT_FOUND.format(', '.join(map(str, missing_ids))))

    def update_owner(self, own, all_data, messages):
        owner_id = own.get('id')
        try:
            existing_owner = OwnerInfo.objects.get(id=owner_id)
        except OwnerInfo.DoesNotExist:
            raise NotFound(Error.OWNER_ID_NOT_FOUND.format(owner_id))

        for field, value in own.items():
            if field not in ['id', 'owners', 'property', 'registered']:
                if field == 'email' and value != existing_owner.email:
                    if OwnerInfo.objects.filter(email=value, property=existing_owner.property).exists():
                        messages.append(Error.EMAIL_ALREADY_ASSIGNED.format(value))
                    else:
                        setattr(existing_owner, field, value)
                else:
                    setattr(existing_owner, field, value)
        existing_owner.save()
        own_serializer = OwnerInfoRetrieveSerializer(existing_owner)
        all_data.append(own_serializer.data)


class PropertyDocumentViewSet(GeneralViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    parser_classes = [FormParser, MultiPartParser]


class CalendarSlotViewSet(GeneralViewSet):
    queryset = CalendarSlot.objects.all()
    serializer_class = CalendarSlotSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of all dates for a specific month and year.
        """
        serializer = CalendarSlotListSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        month = data.get('month')
        year = data.get('year')
        property = data.get('property')
        unit = data.get('unit')

        if not month or not year:
            return CustomResponse({"error": "Month and Year are required"}, status=400)

        # Generate the first and last day of the month
        start_date = datetime(year=int(year), month=int(month), day=1)
        end_date = datetime(year=int(year), month=int(month), day=28)  # To ensure we don't overflow on February
        # Adjust end_date to the last day of the month
        while True:
            try:
                end_date = end_date.replace(day=28) + timedelta(days=4)  # this will always get us to the next month
                end_date = end_date - timedelta(days=end_date.day)
                break
            except ValueError:
                pass

        slots = CalendarSlot.objects.filter(date__gte=start_date, date__lte=end_date, property=property, unit=unit)

        # Create a list of all dates of the month, defaulting to available
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            status = 'available'
            # Check if the date is in the database and has a status of 'unavailable'
            existing_slot = slots.filter(date=current_date).first()
            if existing_slot:
                status = existing_slot.status
            all_dates.append({
                'id': existing_slot.id if existing_slot else None,
                'date': current_date.strftime('%Y-%m-%d'),
                'status': status,
                'reason': existing_slot.reason if existing_slot else None
            })
            current_date += timedelta(days=1)

        return CustomResponse({"data": all_dates})

    def create(self, request, *args, **kwargs):
        """
        Create unavailable slots based on provided dates.
        """
        property = request.data.get('property')
        unit = request.data.get('unit')
        data_ = request.data.get('unavailable_dates')

        if not data_:
            return CustomResponse({"error": Error.UNAVAILABLE_DATES_REQUIRED}, status=400)

        for data in data_:
            data['status'] = 'unavailable'
            data['property'] = property
            data['unit'] = unit
            serializer = self.serializer_class(data=data)
            if serializer.is_valid(raise_exception=True):
                CalendarSlot.objects.create(**serializer.validated_data)

        return CustomResponse({"message": Success.UNAVAILABILITY_SET}, status=201)


class UnitInfoViewSet(GeneralViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    pagination_class = UnitsPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UnitFilter
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # This update is with 'put' method and property id in url
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = UnitUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        existing_photos = serializer.validated_data.pop('existing_photos', [])
        # delete every photo _not_ in the keep-list
        PropertyPhoto.objects.filter(unit=serializer.instance).exclude(id__in=existing_photos).delete()
        # add new photos
        photos = request.FILES.getlist('photo') if request else []
        for photo in photos:
            PropertyPhoto.objects.create(property=serializer.instance.property, unit=serializer.instance, photo=photo)
        self.perform_update(serializer)
        return CustomResponse({
            'message': Success.UNIT_INFO_UPDATED,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='publish', permission_classes=[IsAuthenticated, IsKYCApproved, IsUnitOwner])
    def publish(self, request, pk=None):
        try:
            unit = self.get_object()
        except Property.DoesNotExist:
            return CustomResponse({"error": Error.UNIT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        published = request.data.get('published', None)

        if published is None:
            return CustomResponse({"error": Error.PUBLISHED_FIELD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        unit.published = published
        unit.published_at = datetime.now() if published else None
        unit.save()

        serializer = self.get_serializer(unit)

        return CustomResponse({"message": Success.UNIT_PUBLISHED_STATUS, "data": serializer.data},
                              status=status.HTTP_200_OK)

    def get_queryset(self):
        property_id = self.request.query_params.get('property')
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)
        return self.queryset.filter(property=property_id)

    def get_object(self):
        try:
            unit = Unit.objects.get(id=self.kwargs['pk'])
            # Ensure user owns the property
            if hasattr(self.request, 'user') and unit.property.property_owner != self.request.user:
                raise PermissionDenied(Error.UNIT_NOT_OWNED)
            return unit
        except Unit.DoesNotExist:
            raise NotFound(Error.UNIT_NOT_FOUND)


class PropertyDocumentViewSet2(APIView):
    serializer_class = DocumentCreateSerializer
    pagination_class = DocumentsPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = DocumentFilter
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    @staticmethod
    def check_document_types(property_id, unit_id, data):
        document_types = [item['document_type'] for item in data]
        document_types_to_check = [doc_type for doc_type in document_types if doc_type != 'other']
        existing_documents = PropertyDocument.objects.filter(
            Q(property_id=property_id) & Q(unit_id=unit_id) & Q(document_type__in=document_types_to_check)
        )
        if existing_documents.exists():
            raise ValidationError(
                Error.DOCUMENT_TYPE_EXISTS_V2.format(', '.join([e.document_type for e in existing_documents])))

    def post(self, request):
        existing_data = request.data.get('existing_data')
        data_to_update = []
        if request.data.get('existing_data'):
                data_to_update = json.loads(existing_data).get('data') if existing_data else []
        updated_call = False
        serializer = UploadDocumentFormSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return CustomResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        property_id = serializer.validated_data['property']
        unit_id = serializer.validated_data.get('unit')
        page_saved = serializer.validated_data['page_saved']
        data = serializer.validated_data['data']['data']

        obj = get_object_or_404(Property, id=property_id)

        # self.check_document_types(property_id, unit_id, data)

        if data_to_update:
            self.check_document_exists_update_case(data_to_update, property_id=obj.id, unit_id=unit_id)
        self.check_document_exists_create_case(data, property_id=obj.id, unit_id=unit_id)

        saved_documents = []
        # for new documents
        if data:
            documents = serializer.validated_data.get('documents')
            if not documents:
                return CustomResponse({"error": Error.DOCUMENTS_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
            if len(data) != len(documents):
                return CustomResponse({"error": Error.DOCUMENT_DETAIL_MISSING},
                                      status=status.HTTP_400_BAD_REQUEST)

            for index, item in enumerate(data):
                document_data = item
                document_file = documents[index]
                self.create_document(document_data, document_file, saved_documents, property_id, unit_id)
        # for existing documents to edit
        if data_to_update:
            for docs in data_to_update:
                document_data = docs
                if document_data.get('id'):
                    self.update_document(document_data, saved_documents)
                    updated_call = True

            if unit_id:
                obj = get_object_or_404(Unit, id=unit_id)

            if not updated_call:
                obj.page_saved = page_saved
                obj.save(update_fields=['page_saved'])

        return CustomResponse({"data": saved_documents}, status=status.HTTP_201_CREATED)

    def check_document_exists_update_case(self, data, property_id, unit_id):
        existing_docs_ids = [d.get('id') for d in data if d.get('id')]
        existing_docs = PropertyDocument.objects.filter(id__in=existing_docs_ids,
                                                        property=property_id,
                                                        unit=unit_id)

        # Check if all IDs from payload exist in database
        db_doc_ids = set(existing_docs.values_list('id', flat=True))
        missing_ids = set(existing_docs_ids) - db_doc_ids

        if missing_ids:
            raise ValidationError(Error.DOC_ID_NOT_FOUND.format(', '.join(map(str, missing_ids))))

    def check_document_exists_create_case(self, data, property_id, unit_id):
        document_types = [item['document_type'] for item in data if not item.get('id')]
        document_types_to_check = [doc_type for doc_type in document_types if doc_type != 'other']
        existing_documents = PropertyDocument.objects.filter(
            Q(property_id=property_id) & Q(unit_id=unit_id) & Q(document_type__in=document_types_to_check)
        )
        if existing_documents.exists():
            raise ValidationError(
                Error.DOCUMENT_TYPE_EXISTS_V2.format(', '.join([e.document_type for e in existing_documents])))

    def update_document(self, document_data, saved_documents):
        property_document = PropertyDocument.objects.get(id=document_data.get('id'))
        # property_document.document = document_file
        property_document.title = document_data.get('title') if document_data.get('title') else property_document.title
        property_document.visibility = document_data.get('visibility') if document_data.get('visibility') else property_document.visibility
        property_document.save()
        property_document_serialized = DocumentRetrieveSerializer(property_document)
        saved_documents.append(property_document_serialized.data)

    def create_document(self, document_data, document_file, saved_documents, property_id, unit_id):
        req_data = {"unit": unit_id,
                    "property": property_id,
                    "document": document_file,
                    "title": document_data.get('title'),
                    "visibility": document_data.get('visibility'),
                    "document_type": document_data.get('document_type')}

        serializer = self.serializer_class(data=req_data)
        serializer.is_valid(raise_exception=True)

        property_document = PropertyDocument.objects.create(**serializer.validated_data)

        property_document_serialized = DocumentRetrieveSerializer(property_document)
        saved_documents.append(property_document_serialized.data)

    def delete(self, request, *args, **kwargs):
        document_id = kwargs.get('id')
        try:
            document = PropertyDocument.objects.get(id=document_id)
        except PropertyDocument.DoesNotExist:
            return CustomResponse({"error": Error.DOCUMENT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if document.property.property_owner != request.user:
            return CustomResponse({"error": Error.DOCUMENT_DELETE_PERMISSION},
                                status=status.HTTP_403_FORBIDDEN)

        document.delete()

        return CustomResponse({"message": Success.DOCUMENT_DELETED}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)
        unit_id = request.query_params.get('unit')

        queryset = PropertyDocument.objects.filter(property=property_id, unit=unit_id)

        filterset = self.filterset_class(request.query_params, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        paginator = self.pagination_class()

        if not queryset.exists():
            return CustomResponse({"message": Success.DOCUMENTS_LIST, 'data': []}, status=status.HTTP_200_OK)

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            return paginator.get_paginated_response(DocumentRetrieveSerializer(page, many=True).data)

        all_data = DocumentRetrieveSerializer(queryset, many=True).data
        return CustomResponse({"message": Success.DOCUMENTS_LIST, 'data': all_data}, status=status.HTTP_200_OK)


class PropertyDocumentTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        unit_id = request.query_params.get('unit', None)
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)

        try:
            property_instance = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        property_type_ = property_instance.property_type
        if property_type_ == 'university_housing':
            document_types = PropertyDocument.DOCUMENT_TYPE_BY_PROPERTY_TYPE.get('university_housing')
        else:
            document_types = PropertyDocument.DOCUMENT_TYPE_BY_PROPERTY_TYPE.get('others')

        all_types = [choice[0] for choice in document_types]

        existing = set(
            PropertyDocument.objects
                .filter(property_id=property_id, unit_id=unit_id)
                .values_list('document_type', flat=True)
        )

        missing = [t for t in all_types if t not in existing and t != 'other']
        missing.append('other')

        return CustomResponse({"data": missing}, status=status.HTTP_200_OK)


class CostFeeTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        unit_id = request.query_params.get('unit', None)
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)

        try:
            filtered_options = self.get_filtered_cost_fee_options(property_id, unit_id)

            return CustomResponse({"data": filtered_options, "message": Success.COST_FEE_TYPES},
                                  status=status.HTTP_200_OK)
        except Exception as e:
            return CustomResponse({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def get_filtered_cost_fee_options(self, property_id, unit_id):
        cost_fee_categories = CostFeesCategory.objects.filter(property_id=property_id, unit_id=unit_id)

        existing_fees = set(
            CostFee.objects.filter(category__in=cost_fee_categories).values_list('fee_name', flat=True)
        )

        # Get property type to determine which cost fee options to use
        try:
            property_obj = Property.objects.get(id=property_id)
            property_type = property_obj.property_type
        except Property.DoesNotExist:
            raise NotFound(Error.PROPERTY_NOT_FOUND)

        # Use property-specific options if available, otherwise use 'others'
        property_cost_options = cost_fee_options.get(property_type, cost_fee_options.get('others', {}))

        filtered_cost_fee_options = {}
        for category, fee_names in property_cost_options.items():
            filtered_cost_fee_options[category] = [fee for fee in fee_names if fee not in existing_fees]

        return filtered_cost_fee_options


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

            total_units_allowed = int(property_instance.listing_info.number_of_units if property_instance.listing_info.number_of_units else 0)
            number_of_units_to_add = len(processed_data.get(sheet_name_uq).keys())
            existing_units_number = int(property_instance.unit_property.count() if property_instance.unit_property.count() else 0)
            if total_units_allowed < (number_of_units_to_add + existing_units_number):
                raise ValidationError(Error.NUMBER_OF_UNITS_MISMATCH.format(total_units_allowed, existing_units_number, number_of_units_to_add))

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
                        Amenities.objects
                        .annotate(
                            normalized_sub=Lower(
                                Replace(
                                    F("sub_amenity"),
                                    Value(" "),
                                    Value("_")
                                )
                            )
                        )
                        .filter(normalized_sub__in=amenities_list)
                        .values("id", "sub_amenity")
                    )

                    sub_amenities_ids = [item['id'] for item in existing_amenities]
                    sub_amenities_names = snake_case([item['sub_amenity'] for item in existing_amenities])

                    other_amenities = [amenity for amenity in amenities_list if amenity not in sub_amenities_names]

                    bulk_list = []
                    for sub_id in sub_amenities_ids:
                        sub_obj = get_object_or_404(Amenities, id=sub_id)

                        pa = PropertyAssignedAmenities(
                            property=property_instance,
                            sub_amenity=sub_obj,
                            unit=unit_instance
                        )
                        bulk_list.append(pa)

                    PropertyAssignedAmenities.objects.bulk_create(bulk_list)

                    unit_instance.other_amenities = other_amenities
                    unit_instance.page_saved = 3
                    unit_instance.save()
                else:
                    unit_errors[unsnake_case(unit_key)].append(f"Amenities were not found in the file. Edit the unit from Inactive units tab.")


                cost_fee = processed_data.get('cost_fee')
                cost_fee_detail = cost_fee.get(unit_key)
                if cost_fee_detail:
                    for cost in cost_fee_detail:
                        cost_obj = dict()
                        cost_obj['property'] = property_instance
                        cost_obj['unit'] = unit_instance
                        cost_obj['category_name'] = cost.get('category_name')
                        category_obj = CostFeesCategory.objects.filter(property=property_instance, unit=unit_instance,
                                                                            category_name=cost.get('category_name')).first()
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
                    unit_errors[unsnake_case(unit_key)].append(f"Cost fee was not found in the file. Edit the unit from Inactive units tab.")


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
                    if document_url and isinstance(document_url, str) and (document_url.startswith('http://') or document_url.startswith('https://')):
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
                'data': unit_errors
            }

            if unit_success_count == total_units:
                return CustomResponse({'data': response_dict, 'message': Success.ALL_UNITS_CREATED},
                                      status=status.HTTP_201_CREATED)
            else:
                unit_errors_ = f"Error in units; {', '.join(list(unit_errors.keys()))}."
                return CustomResponse({'data': response_dict, 'message': Error.SOME_UNITS_NOT_CREATED.format(
                    unit_success_count, total_units-unit_success_count), 'error': unit_errors_},
                                      status=status.HTTP_201_CREATED)

        else:
            return CustomResponse({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DeleteAllPropertiesView(APIView):
    """
    API view to delete all properties belonging to the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        Property.objects.filter(property_owner=user).delete()
        return CustomResponse({}, status=status.HTTP_200_OK)


class UserPropertiesAndUnitsView(APIView):
    """
    API view to get vacant properties and units for the authenticated user.
    For single family homes: returns vacant properties only
    For other property types: returns vacant units only
    Supports search functionality for property name, unit number, and type.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [CustomSearchFilter]
    search_fields = ['name', 'number', 'type']

    def get_queryset(self):
        """Get the base queryset of properties and units for the authenticated user"""
        user = self.request.user
        result_data = []

        properties = Property.objects.filter(property_owner=user)

        for property_instance in properties:
            if property_instance.property_type == 'single_family_home':
                if property_instance.status == 'vacant':
                    result_data.append({
                        'id': property_instance.id,
                        'name': property_instance.name,
                        'type': 'property'
                    })
            else:
                units = Unit.objects.filter(property=property_instance, status='vacant')
                for unit in units:
                    result_data.append({
                        'id': unit.id,
                        'name': f"{unit.number} - {property_instance.name}",
                        'type': 'unit'
                    })

        return result_data

    def filter_queryset(self, queryset):
        """Apply filters to queryset using filter_backends"""
        search_query = self.request.query_params.get('q', '').strip()

        if search_query:
            filtered_data = []
            search_lower = search_query.lower()

            for item in queryset:
                # Search in name and type fields (following search_fields pattern)
                if (search_lower in item['name'].lower() or
                    search_lower in item['type'].lower()):
                    filtered_data.append(item)

            return filtered_data

        return queryset

    def get(self, request):
        """Get list of user properties and units with pagination and search"""
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)

        # Apply pagination
        paginator = UserPropertiesAndUnitsPagination()
        result_page = paginator.paginate_queryset(filtered_queryset, request)

        if result_page is not None:
            serializer = UserPropertyUnitSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination fails
        serializer = UserPropertyUnitSerializer(filtered_queryset, many=True)
        return CustomResponse({
            'data': serializer.data,
            'message': Success.USER_PROPERTIES_AND_UNITS_LIST
        }, status=status.HTTP_200_OK)