from django.db import models

from .property import Property
from .unit import Unit


class PropertyDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_documents')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_documents', null=True, default=None)
    document = models.FileField(upload_to='property_documents/')
    title = models.CharField(max_length=255)
    DOCUMENT_TYPE_BY_PROPERTY_TYPE = {
        'university_housing': [
            ('lease_agreement', 'Lease Agreement'),
            ('floor_plan', 'Floor Plan'),
            ('compliance_certificate', 'Compliance Certificate'),
            ('maintenance_log', 'Maintenance Log'),
            ('move_in_move_out_checklist', 'Move-In/Move-Out Checklist'),
            ('utility_bill_copy', 'Utility Bill Copy'),
            ('inspection_report', 'Inspection Report'),
            ('renovation_permit', 'Renovation Permit'),
            ('other', 'Other'),
        ],
        'others': [
            ('lease_agreement', 'Lease Agreement'),
            ('medical_clearance_form', 'Medical Clearance Form'),
            ('care_plan_agreement', 'Care Plan Agreement'),
            ('emergency_contact_form', 'Emergency Contact Form'),
            ('medication_schedule', 'Medication Schedule'),
            ('ada_compliance_certificate', 'ADA Compliance Certificate'),
            ('fall_risk_assessment', 'Fall Risk Assessment'),
            ('service_log', 'Service Log'),
            ('insurance_verification', 'Insurance Verification'),
            ('other', 'Other'),
        ],
    }
    document_type_by_choices = [
        ('lease_agreement', 'Lease Agreement'),
        ('medical_clearance_form', 'Medical Clearance Form'),
        ('care_plan_agreement', 'Care Plan Agreement'),
        ('emergency_contact_form', 'Emergency Contact Form'),
        ('medication_schedule', 'Medication Schedule'),
        ('ada_compliance_certificate', 'ADA Compliance Certificate'),
        ('fall_risk_assessment', 'Fall Risk Assessment'),
        ('service_log', 'Service Log'),
        ('insurance_verification', 'Insurance Verification'),
        ('other', 'Other'),
        # university_housing
        ('floor_plan', 'Floor Plan'),
        ('compliance_certificate', 'Compliance Certificate'),
        ('maintenance_log', 'Maintenance Log'),
        ('move_in_move_out_checklist', 'Move-In/Move-Out Checklist'),
        ('utility_bill_copy', 'Utility Bill Copy'),
        ('inspection_report', 'Inspection Report'),
        ('renovation_permit', 'Renovation Permit'),
    ]
    document_type = models.CharField(max_length=100, choices=document_type_by_choices)
    visibility_choices = [
        ('private', 'Private'),
        ('shared', 'Shared with Tenant'),
    ]
    visibility = models.CharField(max_length=20, choices=visibility_choices, default='private')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} for {self.property.name}"
