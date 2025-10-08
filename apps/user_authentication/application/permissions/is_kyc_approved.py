from rest_framework import permissions

class IsKYCApproved(permissions.BasePermission):
    message = "Your KYC verification is not approved. Please complete your KYC verification to perform this action."

    def has_permission(self, request, view):
        return request.user.kyc_user.filter(status='approved').exists()