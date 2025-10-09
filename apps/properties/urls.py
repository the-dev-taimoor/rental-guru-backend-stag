from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.properties.interface.views import (PropertyViewSet, ListingInfoViewSet, RentalDetailViewSet, AmenitiesView, CostFeeViewSet,
                    PropertyOwnerViewSet, PropertyDocumentViewSet, CalendarSlotViewSet, UnitInfoViewSet,
                    PropertyDocumentViewSet2, PropertyRetrieveViewSet, PropertyMetricsViewSet, UnitSummaryViewSet,
                    PropertyDocumentTypesView, CostFeeTypesView, BulkUnitImportAPIView, DeleteAllPropertiesView,
                    TopListingsViewSet, UserPropertiesAndUnitsView)

router = DefaultRouter()
router.register(r'summary', PropertyRetrieveViewSet, basename='property_details')
router.register(r'unit-summary', UnitSummaryViewSet, basename='unit_details')
router.register(r'metrics', PropertyMetricsViewSet, basename='property_metrics')
router.register(r'detail', PropertyViewSet, basename='detail')
router.register(r'top-listings', TopListingsViewSet, basename='top_listings')
router.register(r'listing', ListingInfoViewSet, basename='listing')
router.register(r'rental', RentalDetailViewSet, basename='rental')
router.register(r'amenities', AmenitiesView, basename='amenities')
router.register(r'document', PropertyDocumentViewSet, basename='document')
router.register(r'availability', CalendarSlotViewSet, basename='availability')

router.register(r'unit', UnitInfoViewSet, basename='unit')

urlpatterns = [
    path('', include(router.urls)),
    path('documents/', PropertyDocumentViewSet2.as_view(), name='upload_document'),
    path('documents/<int:id>/', PropertyDocumentViewSet2.as_view(), name='delete_document'),

    path(r'document-types/', PropertyDocumentTypesView.as_view(), name='document_types'),
    path(r'cost-fee-types/', CostFeeTypesView.as_view(), name='cost_fee_types'),

    path(r'units-bulk-import/', BulkUnitImportAPIView.as_view(), name='units_bulk_import'),

    path('cost-fee/', CostFeeViewSet.as_view(), name='cost_fee'),
    path('owner-info/', PropertyOwnerViewSet.as_view(), name='owner_info'),

    # only for testing
    path('user-listings/', DeleteAllPropertiesView.as_view(), name='delete_user_listings'),

    # User properties and units list
    path('user-properties-units/', UserPropertiesAndUnitsView.as_view(), name='user_properties_units'),
]
