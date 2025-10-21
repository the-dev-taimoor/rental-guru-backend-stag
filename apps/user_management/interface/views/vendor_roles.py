from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.user_management.infrastructure.models import VendorInvitation
from common.constants import Success
from common.utils import CustomResponse


class VendorRolesView(APIView):
    """
    API view to get available vendor roles.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        roles = []
        for role_value, role_display in VendorInvitation.VENDOR_ROLE_CHOICES:
            roles.append({'value': role_value, 'label': role_display})

        return CustomResponse({"message": Success.VENDOR_ROLES_LIST, "data": roles}, status=status.HTTP_200_OK)
