from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.properties.infrastructure.models import Invitation, OwnerInfo, Property
from apps.properties.interface.serializers import OwnerInfoRetrieveSerializer, OwnerInfoSerializer
from common.constants import Error, Success
from common.utils import CustomResponse, send_email_


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
