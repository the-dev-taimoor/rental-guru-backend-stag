from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

class Property(models.Model):
    property_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_owner')
    property_type_by_choices = [
        ('single_family_home', "Single-Family Home"),
        ('apartment_unit', "Apartment Unit"),
        ('multi_family', "Multi-Family"),
        ('student_housing', "Student Housing"),
        ('senior_living', "Senior Living"),
        ('university_housing', "University Housing"),
    ]
    status_by_choices = [
        ('vacant', "Vacant"),
        ('occupied', "Occupied"),
    ]
    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=50, choices=property_type_by_choices)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='vacant', choices=status_by_choices)

    # Other amenities (tags)
    other_amenities = models.JSONField(blank=True, null=True, help_text="List of other amenities")

    page_saved = models.IntegerField(default=1)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    status_by_choices = [
        ('vacant', "Vacant"),
        ('occupied', "Occupied"),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='unit_property')
    number = models.CharField(max_length=20)
    type = models.CharField(max_length=20)
    floor_number = models.CharField(max_length=20, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    beds = models.PositiveIntegerField(default=0)
    desks = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='vacant', choices=status_by_choices)

    other_amenities = models.JSONField(blank=True, null=True, help_text="List of other amenities")

    csv_upload = models.IntegerField(default=0)
    page_saved = models.IntegerField(default=1)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.number


class ListingInfo(models.Model):
    property_listed_by_choices = [
        ('owner_manager_not_live', "I'm the property owner/manager and don't live on the property"),
        ('owner_manager_live', "I'm the property owner/manager and do live on the property"),
        ('agent_broker', "I'm an agent/broker/management company and don't live on the property"),
    ]
    availability_duration_by_choices = [
        (30, "30 mins"),
        (60, "1 Hour"),
        (90, "1.5 Hours"),
        (120, "2 Hours"),
    ]

    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='listing_info')
    listed_by = models.CharField(max_length=50, choices=property_listed_by_choices)
    total_bedrooms = models.PositiveIntegerField(blank=True, null=True)
    total_bathrooms = models.PositiveIntegerField(blank=True, null=True)
    square_footage = models.PositiveIntegerField(blank=True, null=True, help_text='Size in sq.ft.')
    number_of_units = models.PositiveIntegerField(blank=True, null=True)
    # for university_housing only
    occupancy_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('single', "Single"),
        ('shared', "Shared"),
        ('mixed', "Mixed"),
    ])

    description = models.TextField()

    care_services = models.JSONField(default=list, blank=True, null=True)

    pets_allowed = models.BooleanField(default=False)
    pet_types = models.JSONField(blank=True, null=True, help_text="List of allowed pet types")
    other_pets = models.JSONField(blank=True, null=True, help_text="List of allowed pet types")

    availability_duration = models.IntegerField(default=30, choices=availability_duration_by_choices,
                                                help_text="Availability time duration.")
    showing_availability = models.JSONField(help_text="Availability to show the property")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Listing Info for {self.property.name}"


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_photos')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_photos', null=True, default=None)
    photo = models.ImageField(upload_to='property_photos/', max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Photo of {self.property.name}"


class RentDetails(models.Model):
    rental_type_by_choices = [
        ('short_term', "Short-Term (Daily/Weekly)"),
        ('long_term', "Long-Term (Monthly/Annual)"),
        ('monthly_billing', "Monthly Billing"), # university_housing
        ('semester_billing', "Semester Billing"), # university_housing
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_rent_details')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_rent_details', null=True, default=None)
    # tenant FK needs to be here
    assigned_tenant = models.CharField(max_length=100, blank=True, null=True)
    rental_type = models.CharField(max_length=50, choices=rental_type_by_choices)
    semester = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('fall', "Fall"),
        ('spring', "Spring"),
        ('summer', "Summer"),
    ])
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    lease_start_date = models.DateField(blank=True, null=True)
    lease_end_date = models.DateField(blank=True, null=True)
    promote_special_offer = models.BooleanField(default=False)
    offer_start_date = models.DateField(blank=True, null=True)
    offer_end_date = models.DateField(blank=True, null=True)
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'unit')

    def __str__(self):
        return f"Rent Details for {self.property.name}"


class Amenities(models.Model):
    amenity = models.CharField(max_length=100)
    sub_amenity = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PropertyTypeAndAmenity(models.Model):
    sub_amenities = models.ForeignKey(Amenities, on_delete=models.CASCADE, related_name='sub_amenities')
    property_type = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PropertyAssignedAmenities(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_amenities', null=True, default=None)
    sub_amenity = models.ForeignKey(Amenities, on_delete=models.CASCADE, related_name='assigned_sub_amenity')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Amenities for {self.property.name}"


class CostFeesCategory(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_cost_fee_categories')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_cost_fee_categories', null=True, default=None)
    category_name = models.CharField(max_length=100)  # e.g., Parking, Utilities, Other Categories

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category_name} costs for {self.property.name}"


class CostFee(models.Model):
    category = models.ForeignKey(CostFeesCategory, on_delete=models.CASCADE, related_name='fees')
    fee_name = models.CharField(max_length=100)
    payment_frequency_by_choices = [
        ('one_time', "One Time"),
        ('monthly', "Monthly"),
        ('per_use', "Per Use"),
        ('quarterly', "Quarterly"), # university_housing
        ('yearly', "Yearly"), # university_housing
    ]
    payment_frequency = models.CharField(max_length=50, choices=payment_frequency_by_choices)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fee_type_by_choices = [
        ('flat_fee', "Flat Fee"),
        ('flat_fee_per_item', "Flat Fee Per Item"),
        ('fee_range', "Fee Range"),
    ]
    fee_type = models.CharField(max_length=50, choices=fee_type_by_choices)
    required_status_choices = [
        ('in_rent', 'Included in base rent'),
        ('required', 'Required'),
        ('optional', 'Optional'),
    ]
    is_required = models.CharField(max_length=50, choices=required_status_choices)
    refundable_status_choices = [
        ('non_refundable', 'Non-refundable'),
        ('partially_refundable', 'Partially refundable'),
        ('refundable', 'Refundable'),
    ]
    refundable_status = models.CharField(max_length=50, blank=True, null=True, choices=refundable_status_choices)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('category', 'fee_name')

    def __str__(self):
        return f"{self.fee_name} in {self.category.category_name}"


class OwnerInfo(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_owned')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_detail') # one who is inviting
    email = models.EmailField()
    percentage = models.CharField(max_length=10)
    emergency_person = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)

    registered = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'owner', 'email')

    def __str__(self):
        return f"Owner info for {self.property.name}"


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


class CalendarSlot(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_slots')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_slots', null=True, default=None)
    date = models.DateField()
    status = models.CharField(
        max_length=50,
        choices=[('available', 'Available'), ('unavailable', 'Unavailable')]
    )
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.status}"


class Invitation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    receiver_email = models.EmailField()
    role = models.CharField(max_length=50)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)