from rest_framework import permissions


class IsUnitOwner(permissions.BasePermission):
    message = "You do not have permission to perform this action on this unit."

    def has_permission(self, request, view):
        unit_id = view.kwargs.get('pk')
        from apps.properties.infrastructure.models import Unit

        try:
            unit = Unit.objects.get(id=unit_id)
            return request.user.property_owner.filter(id=unit.property.id).exists()
        except Unit.DoesNotExist:
            return False
