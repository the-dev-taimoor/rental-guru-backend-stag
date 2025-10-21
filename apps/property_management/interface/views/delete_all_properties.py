from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.property_management.infrastructure.models import Property
from common.utils import CustomResponse


class DeleteAllPropertiesView(APIView):
    """
    API view to delete all properties belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        Property.objects.filter(property_owner=user).delete()
        return CustomResponse({}, status=status.HTTP_200_OK)
