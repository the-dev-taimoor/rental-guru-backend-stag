from common.pagination.base_pagination import BasePagination
from common.constants import Success

class KYCRequestsPagination(BasePagination):
    message= Success.KYC_LIST

class TenantInvitationPagination(BasePagination):
    message = Success.TENANT_INVITATIONS_LIST

class VendorInvitationPagination(BasePagination):
    message = Success.VENDOR_INVITATIONS_LIST
