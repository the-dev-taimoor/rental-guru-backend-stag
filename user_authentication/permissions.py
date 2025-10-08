from rest_framework import permissions

class IsKYCApproved(permissions.BasePermission):
    message = "Your KYC verification is not approved. Please complete your KYC verification to perform this action."

    def has_permission(self, request, view):
        return request.user.kyc_user.filter(status='approved').exists()

class IsPropertyOwner(permissions.BasePermission):
    message = "You do not have permission to perform this action on this property."

    def has_permission(self, request, view):
        property_id = view.kwargs.get('pk')
        return request.user.property_owner.filter(id=property_id).exists()


class IsUnitOwner(permissions.BasePermission):
    message = "You do not have permission to perform this action on this unit."

    def has_permission(self, request, view):
        unit_id = view.kwargs.get('pk')
        from properties.models import Unit
        try:
            unit = Unit.objects.get(id=unit_id)
            return request.user.property_owner.filter(id=unit.property.id).exists()
        except Unit.DoesNotExist:
            return False
