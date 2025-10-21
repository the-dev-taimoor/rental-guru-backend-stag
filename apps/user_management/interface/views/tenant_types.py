from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import TenantInvitation
from common.utils import CustomResponse


class TenantTypesView(APIView):
    """
    API view to get all available tenant types.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get list of all tenant types"""
        tenant_types = []
        for tenant_type_value, tenant_type_display in TenantInvitation.TENANT_TYPE_CHOICES:
            tenant_types.append({'value': tenant_type_value, 'label': tenant_type_display})

        return CustomResponse({"message": "Tenant types retrieved successfully.", "data": tenant_types}, status=status.HTTP_200_OK)
