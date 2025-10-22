from collections import defaultdict

from rest_framework import serializers

from apps.user_management.infrastructure.models import ServiceSubCategory, Vendor, VendorService
from common.utils import get_presigned_url


class VendorProfileSerializer(serializers.ModelSerializer):
    services_offered = serializers.JSONField(write_only=True)
    services = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.profile_image_path.name:
            rep["profile_image_path"] = get_presigned_url(instance.profile_image_path.name)
        return rep

    def get_services(self, obj):
        vendor_services = VendorService.objects.filter(user_id=obj.user_id).select_related('category_id', 'subcategory_id')

        category_dict = defaultdict(list)
        for vs in vendor_services:
            category_name = vs.category_id.name
            subcategory_name = vs.subcategory_id.name
            category_dict[category_name].append(subcategory_name)

        return dict(category_dict)

    def create(self, validated_data):
        services_offered = validated_data.pop('services_offered', [])
        instance = super().create(validated_data)

        user = validated_data.get('user_id')
        VendorService.objects.filter(user_id=user).delete()

        for subcat_id in services_offered:
            try:
                subcategory = ServiceSubCategory.objects.get(id=subcat_id)
            except ServiceSubCategory.DoesNotExist:
                continue

            VendorService.objects.create(user_id=user, category_id=subcategory.category_id, subcategory_id=subcategory)
        return instance
