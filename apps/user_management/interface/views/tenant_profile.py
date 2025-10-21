from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.user_management.infrastructure.models import Role, Tenant
from apps.user_management.interface.serializers import TenantProfileSerializer
from common.constants import Success
from common.utils import CustomResponse

from .property_owner_profile import PropertyOwnerProfileView


class TenantProfileView(PropertyOwnerProfileView):
    """
    API view to create and update a tenant profile.
    """

    serializer = TenantProfileSerializer
    model = Tenant
    role = 'tenant'

    @swagger_auto_schema(request_body=serializer, responses={201: Success.PROFILE_SETUP})
    def post(self, request):
        data = request.data.copy()
        data['user_id'] = request.user.id

        serializer = self.serializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                Role.objects.create(user_id=request.user, role=self.role)
            return CustomResponse({'data': serializer.data, 'message': Success.PROFILE_SETUP}, status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)

    def patch(self, request):
        """
        Update tenant profile.
        """
        profile = get_object_or_404(self.model, user_id=request.user.id)
        serializer = self.serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse({'data': serializer.data, 'message': Success.PROFILE_UPDATED}, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)
