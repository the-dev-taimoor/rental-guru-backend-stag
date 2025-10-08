from rest_framework import permissions

class IsPropertyOwner(permissions.BasePermission):
    message = "You do not have permission to perform this action on this property."

    def has_permission(self, request, view):
        property_id = view.kwargs.get('pk')
        return request.user.property_owner.filter(id=property_id).exists()