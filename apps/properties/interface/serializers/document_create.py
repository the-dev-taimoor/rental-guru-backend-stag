from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.properties.infrastructure.models import PropertyDocument
from common.constants import Error
from common.utils import get_presigned_url


class DocumentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyDocument
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.document.name:
            rep["document"] = get_presigned_url(instance.document.name)
        return rep

    def validate(self, data):
        property_wise_document_types = {
            'university_housing': [
                'lease_agreement',
                'floor_plan',
                'compliance_certificate',
                'maintenance_log',
                'move_in_move_out_checklist',
                'utility_bill_copy',
                'inspection_report',
                'renovation_permit',
                'other',
            ],
            'others': [
                'lease_agreement',
                'medical_clearance_form',
                'care_plan_agreement',
                'emergency_contact_form',
                'medication_schedule',
                'ada_compliance_certificate',
                'fall_risk_assessment',
                'service_log',
                'insurance_verification',
                'other',
            ],
        }
        unit = data.get('unit')
        property_type = data['property'].property_type
        if property_type == 'university_housing':
            if data['document_type'] not in property_wise_document_types.get('university_housing'):
                raise ValidationError(Error.DOCUMENT_TYPE_UNIVERSITY_HOUSING)
        else:
            if data['document_type'] not in property_wise_document_types.get('others'):
                raise ValidationError(Error.DOCUMENT_TYPE_OTHERS.format(property_type.replace('_', ' ').capitalize()))

        if data['document_type'] != 'other':
            if PropertyDocument.objects.filter(property=data['property'], unit=unit, document_type=data['document_type']).exists():
                raise ValidationError(Error.DOCUMENT_TYPE_EXISTS_V2.format(data['document_type'].replace('_', ' ').capitalize()))
        return data
