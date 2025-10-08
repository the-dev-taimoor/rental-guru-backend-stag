from django.urls import path
from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .models import ServiceCategory
from .views import (SignupView, CustomTokenObtainPairView, CustomTokenRefreshView, OTPView, OTPVerifyView,
                    ForgotPasswordView, ResetPasswordView, LogoutView, PropertyOwnerProfileView, KYCRequests,
                    KYCView, VendorProfileView, KYCRequestDetails, ServiceCategoriesView, ServiceSubCategoriesView,
                    SelectRoleView, VendorInvitationView, VendorRolesView, VendorDetailsByInvitationView,
                    BulkVendorInviteAPIView, TenantProfileView, TenantInvitationView, TenantDetailsByInvitationView,
                    TenantTypesView, InvitationDetailsView, LeaseManagementView, ResendInvitation)
if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()
router.register('service-categories', ServiceCategoriesView)
router.register('service-subcategories', ServiceSubCategoriesView)
urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('user-details/', SignupView.as_view(), name='user-detail'),
    path('add-role/', SelectRoleView.as_view(), name='add_role'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('otp/', OTPView.as_view(), name='otp'),
    path('otp-verify/', OTPVerifyView.as_view(), name='otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('property-owner-profile/', PropertyOwnerProfileView.as_view(), name='property_owner_profile'),
    path('vendor-profile/', VendorProfileView.as_view(), name='vendor_profile'),
    path('tenant-profile/', TenantProfileView.as_view(), name='tenant_profile'),
    path('kyc-request/', KYCRequests.as_view(), name='kyc_request'),
    path('kyc-request-detail/<int:pk>/', KYCRequestDetails.as_view(), name='kyc_request_detail'),
    path('kyc/', KYCView.as_view(), name='kyc_list'),
    path('kyc/stats/', KYCView.as_view(), name='kyc_stats'),

    # Vendor invitation API
    path('invite-vendor/', VendorInvitationView.as_view(), name='invite_vendor'),
    path('invite-vendor/<int:invitation_id>/', VendorInvitationView.as_view(), name='delete_vendor_invitation'),
    path('vendor-roles/', VendorRolesView.as_view(), name='vendor_roles'),
    path('invited-vendor-details/<int:invitation_id>/', VendorDetailsByInvitationView.as_view(), name='vendor_details_by_invitation'),
    path('invite-vendor-bulk/', BulkVendorInviteAPIView.as_view(), name='invite_vendor_bulk'),
    
    # Tenant invitation API
    path('invite-tenant/', TenantInvitationView.as_view(), name='invite_tenant'),
    path('accept-agreement/', TenantInvitationView.as_view(), name='accept_agreement'),
    path('invite-tenant/<int:invitation_id>/', TenantInvitationView.as_view(), name='delete_tenant_invitation'),
    path('tenant-types/', TenantTypesView.as_view(), name='tenant_types'),
    path('invited-tenant-details/<int:invitation_id>/', TenantDetailsByInvitationView.as_view(), name='tenant_details_by_invitation'),
    path('manage-lease/', LeaseManagementView.as_view(), name='manage_lease'),

    # Public invitation details API (no authentication required)
    path('invitation/<int:invitation_id>/', InvitationDetailsView.as_view(), name='invitation_details'),

    path('accept-invitation/', InvitationDetailsView.as_view(), name='accept_invitation'),

    path('resend-invitation/', ResendInvitation.as_view(), name='resend_invitation'),

]
urlpatterns += router.urls