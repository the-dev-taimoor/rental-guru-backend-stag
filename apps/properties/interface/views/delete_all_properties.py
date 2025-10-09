from apps.properties.infrastructure.models import Property
from rest_framework.permissions import IsAuthenticated

from common.utils import CustomResponse
from rest_framework.views import APIView
from rest_framework import status

class DeleteAllPropertiesView(APIView):
    """
    API view to delete all properties belonging to the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        Property.objects.filter(property_owner=user).delete()
        return CustomResponse({}, status=status.HTTP_200_OK)