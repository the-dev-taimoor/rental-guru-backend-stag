from django.contrib.auth import get_user_model
from django.db import models

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

    class Meta:
        app_label = 'properties'

    def __str__(self):
        return self.name
