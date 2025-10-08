from django.db import migrations

def add_amenities_and_property_types(apps, schema_editor):
    Amenities = apps.get_model('properties', 'Amenities')
    PropertyTypeAndAmenity = apps.get_model('properties', 'PropertyTypeAndAmenity')

    # Define amenities and sub-amenities for each property type
    amenities_for_apartment_unit = {
    "Laundry Facilities": [
        "Shared laundry in the building",
        "Shared washer-dryer hookups in the building",
        "No laundry facilities"
    ],
    "Amenities for All Residents": [
        "Elevator",
        "Doorman",
        "Shared Gym",
        "Rooftop Access",
        "Pool",
        "Courtyard",
        "Lounge",
        "Bike Storage",
        "Package Room",
        "Shared Workspace",
        "EV Charging Station",
        "Community Kitchen",
        "Conference Room"
    ],
    "Accessibility Features": [
        "Wheelchair access",
        "Ramps/elevators",
        "Accessible bathroom facilities"
    ],
    "Available Parking Options": [
        "Attached Garage",
        "Detached Garage",
        "Gated Parking",
        "Off-street Parking"
    ]
}


    amenities_for_senior_living = {
    "Safety & Emergency Features": [
        "Emergency Call Buttons in Rooms",
        "Smoke & CO Detectors",
        "On-site Nurse Station",
        "24/7 Staff Presence",
        "Fire Sprinkler System",
        "Non-slip Flooring",
        "Grab Bars in Bathrooms"
    ],
    "Senior Comfort & Accessibility Features": [
        "Wheelchair access",
        "Ramps/elevators",
        "Wide Doorways",
        "Recliner Chairs in Lounge",
        "Ramps for Entryways",
        "Adjustable Beds",
        "Accessible Bathrooms",
        "Climate-Controlled Rooms"
    ],
    "Wellness & Social Features": [
        "Community Dining Room",
        "Activity & Game Room",
        "Library",
        "Garden/Patio",
        "Religious/Spiritual Room",
        "Therapy or Fitness Room",
        "Beauty Salon/Barber",
        "On-site Café"
    ]
}


    amenities_for_student_housing = {
    "Laundry Facilities": [
        "Shared laundry in the building",
        "Shared laundry on each floor",
        "No laundry facilities"
    ],
    "Student Resident Amenities": [
        "Study Rooms",
        "High-Speed Wi-Fi",
        "Common Lounge",
        "Gaming/Recreational Room",
        "Shared Kitchen",
        "Library or Quiet Study Area",
        "Bike Storage",
        "Printing/Copying Station",
        "Security Desk or 24/7 Surveillance"
    ],
    "Accessibility Features": [
        "Wheelchair access",
        "Ramps/elevators",
        "Accessible bathroom facilities"
    ],
    "Roommate Friendly Features": [
        "Shared Bedrooms",
        "Private Bedrooms",
        "Shared Bathrooms",
        "Lockable Bedroom Doors"
    ],
    "Available Parking Options": [
        "Attached Garage",
        "Detached Garage",
        "Gated Parking",
        "Off-street Parking"
    ]
}


    # Add amenities and sub-amenities for single_family_home
    for amenity_name, sub_amenity_names in amenities_for_apartment_unit.items():
        amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_amenity_names[0])  # Just add the first sub-amenity for now
        for sub_name in sub_amenity_names:
            # For each sub-amenity, create a corresponding entry in the Amenities table
            sub_amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_name)
            # Create a PropertyTypeAndAmenity record for apartment_unit
            PropertyTypeAndAmenity.objects.create(sub_amenities=sub_amenity_obj, property_type='apartment_unit')


    # Add amenities and sub-amenities for single_family_home
    for amenity_name, sub_amenity_names in amenities_for_senior_living.items():
        amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_amenity_names[0])  # Just add the first sub-amenity for now
        for sub_name in sub_amenity_names:
            # For each sub-amenity, create a corresponding entry in the Amenities table
            sub_amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_name)
            # Create a PropertyTypeAndAmenity record for senior_living
            PropertyTypeAndAmenity.objects.create(sub_amenities=sub_amenity_obj, property_type='senior_living')

    # Add amenities and sub-amenities for multi_family
    for amenity_name, sub_amenity_names in amenities_for_student_housing.items():
        amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_amenity_names[0])  # Just add the first sub-amenity for now
        for sub_name in sub_amenity_names:
            # For each sub-amenity, create a corresponding entry in the Amenities table
            sub_amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_name)
            # Create a PropertyTypeAndAmenity record for student_housing
            PropertyTypeAndAmenity.objects.create(sub_amenities=sub_amenity_obj, property_type='student_housing')


class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0004_listinginfo_care_services_property_property_owner_and_more'),
    ]

    operations = [
        migrations.RunPython(add_amenities_and_property_types),
    ]
