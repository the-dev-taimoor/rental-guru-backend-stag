from rest_framework import serializers

from apps.user_management.infrastructure.models import LicenseAndCertificates
from common.utils import get_presigned_url, unsnake_case


class LicenseAndCertificatesSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = LicenseAndCertificates
        fields = ['id', 'document', 'title']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
            rep["title"] = unsnake_case(instance.document.name.split('/')[-1].split('.')[0])
        return rep

    def get_title(self, instance):
        return unsnake_case(instance.document.name.split('/')[-1].split('.')[0])
