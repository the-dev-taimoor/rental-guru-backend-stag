from collections import defaultdict

from rest_framework import serializers

from apps.user_management.infrastructure.models import Vendor, VendorServices


class VendorServicesInfoSerializer(serializers.ModelSerializer):
    """Serializer for vendor services information tab"""

    services = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['services', 'service_area', 'description']

    def get_services(self, obj):
        vendor_services = VendorServices.objects.filter(user_id=obj.user_id).select_related('category_id', 'subcategory_id')

        category_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            category_dict[category_name].append(subcategory_name)

        return dict(category_dict)
