from django.db import models
from .property import Property

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