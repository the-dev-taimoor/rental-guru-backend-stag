from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import status, permissions

from common.constants import Success, Error
from common.utils import CustomResponse

from apps.user_authentication.infrastructure.models import Role
from apps.user_authentication.interface.serializers import SelectRoleSerializer


class SelectRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer = SelectRoleSerializer
    model = Role

    def post(self, request):
        data = request.data.copy()
        serializer = self.serializer(data=data)
        if Role.objects.filter(user_id=request.user, role=data.get('role')).exists():
            raise ValidationError(Error.ROLE_ALREADY_ASSIGNED.format(data.get('role').replace('_', ' ').title()))
        if serializer.is_valid(raise_exception=True):
            data['user_id'] = request.user
            data['role'] = serializer.validated_data.get('role')
            Role.objects.create(**data)
        return CustomResponse({'message': Success.ROLE_ADDED}, status=status.HTTP_201_CREATED)