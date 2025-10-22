from django.db import migrations


def add_amenities_and_property_types(apps, schema_editor):
    Amenities = apps.get_model('property_management', 'Amenities')
    PropertyTypeAndAmenity = apps.get_model('property_management', 'PropertyTypeAndAmenity')

    # Step 1: Delete all existing records from both tables only in this migration
    Amenities.objects.all().delete()
    PropertyTypeAndAmenity.objects.all().delete()

    # Step 2: Reset the primary key sequence (id) for both tables
    schema_editor.execute('ALTER SEQUENCE property_management_amenities_id_seq RESTART WITH 1;')
    schema_editor.execute('ALTER SEQUENCE property_management_propertytypeandamenity_id_seq RESTART WITH 1;')

    single_family_home = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared washer-dryer hookups in the building", "No laundry facilities"],
        "Cooling": ["Central", "Wall", "Window"],
        "Heating": ["Baseboard", "Forced air", "Heat pump", "Wall"],
        "Appliances": ["Dishwasher", "Freezer", "Microwave", "Oven"],
        "Flooring": ["Carpet", "Hardwood", "Tile"],
        "Room Setup": ["Room has private bath", "Room is furnished", "Shared space is furnished"],
    }

    multi_family = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared washer-dryer hookups in the building", "No laundry facilities"],
        "Building Amenities": [
            "Backyard or Shared Yard",
            "Shared Patio/Deck",
            "Basement Storage",
            "Shared Garage",
            "Outdoor Grill Area",
            "Private Mailbox Area",
            "Shared Workspace",
            "Garden Space",
            "Common Room or Sitting Area",
        ],
        "Parking": ["Attached Garage", "Detached Garage", "Driveway Parking", "Street Parking"],
        "Accessibility": ["Wheelchair access", "Ramps Entry", "Wide Door Frames", "Ground-Level Access"],
    }

    apartment_unit = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared washer-dryer hookups in the building", "No laundry facilities"],
        "Building Amenities": [
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
            "Conference Room",
        ],
        "Accessibility Features": ["Wheelchair access", "Ramps/elevators", "Accessible bathroom facilities"],
        "Available Parking Options": ["Attached Garage", "Detached Garage", "Gated Parking", "Off-street Parking"],
    }

    senior_living = {
        "Safety & Emergency Features": [
            "Emergency Call Buttons in Rooms",
            "Smoke & CO Detectors",
            "On-site Nurse Station",
            "24/7 Staff Presence",
            "Fire Sprinkler System",
            "Non-slip Flooring",
            "Grab Bars in Bathrooms",
        ],
        "Senior Comfort & Accessibility Features": [
            "Wheelchair access",
            "Ramps/elevators",
            "Wide Doorways",
            "Recliner Chairs in Lounge",
            "Ramps for Entryways",
            "Adjustable Beds",
            "Accessible Bathrooms",
            "Climate-Controlled Rooms",
        ],
        "Wellness & Social Features": [
            "Community Dining Room",
            "Activity & Game Room",
            "Library",
            "Garden/Patio",
            "Religious/Spiritual Room",
            "Therapy or Fitness Room",
            "Beauty Salon/Barber",
            "On-site Café",
        ],
    }

    student_housing = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared laundry on each floor", "No laundry facilities"],
        "Student Resident Amenities": [
            "Study Rooms",
            "High-Speed Wi-Fi",
            "Common Lounge",
            "Gaming/Recreational Room",
            "Shared Kitchen",
            "Library or Quiet Study Area",
            "Bike Storage",
            "Printing/Copying Station",
            "Security Desk or 24/7 Surveillance",
        ],
        "Accessibility Features": ["Wheelchair access", "Ramps/elevators", "Accessible bathroom facilities"],
        "Roommate Friendly Features": ["Shared Bedrooms", "Private Bedrooms", "Shared Bathrooms", "Lockable Bedroom Doors"],
        "Available Parking Options": ["Attached Garage", "Detached Garage", "Gated Parking", "Off-street Parking"],
    }

    multi_family_unit = {
        "Climate & Utility": ["Central Heating", "City Water", "Electricity", "Heat Pump", "Outdoor Kitchen"],
        "Comfort & Living": ["Ensuite Bathroom", "Private Balcony", "Security System", "Fire Security", "Soundproof Walls"],
        "Facilities": ["Garage", "Personal Storage", "Cinema Room"],
    }

    apartment_unit_unit = {
        "Climate & Utility": ["Central Heating", "City Water", "Electricity", "Heat Pump", "Outdoor Kitchen"],
        "Comfort & Living": ["Ensuite Bathroom", "Private Balcony", "Security System", "Fire Security", "Soundproof Walls"],
        "Facilities": ["Garage", "Personal Storage", "Cinema Room"],
    }

    senior_living_unit = {
        "Climate & Utility": ["Central Heating", "City Water", "Electricity", "Heat Pump", "Outdoor Kitchen"],
        "Comfort & Living": ["Ensuite Bathroom", "Private Balcony", "Security System", "Fire Security", "Soundproof Walls"],
        "Facilities": ["Garage", "Personal Storage", "Cinema Room"],
        "Care & Accessibility": [
            "Emergency Call System",
            "Wheelchair Access",
            "Grab Bars in Bathroom",
            "Non-slip Flooring",
            "Adjustable Lighting",
            "Nurse On Call",
            "Medication Storage",
        ],
    }

    student_housing_unit = {
        "Room Furnishing": ["Fully Furnished", "Semi-Furnished", "Not Furnished"],
        "Laundry Access": [
            "Shared laundry in the unit",
            "Shared washer-dryer hookups in the unit",
            "Shared laundry in the building",
            "No laundry facilities",
        ],
        "Amenities": [
            "Study Desk",
            "Wardrobe/Closet",
            "Mini Fridge",
            "Private Bathroom",
            "Shared Bathroom Access",
            "Air Conditioning",
            "Heater",
            "Window with Natural Light",
            "Personal Balcony (if applicable)",
        ],
    }

    # Function to create or get an existing amenity and sub-amenity
    def get_or_create_amenity(amenity_name, sub_amenity_name):
        # Check if the amenity already exists
        amenity_obj, created = Amenities.objects.get_or_create(amenity=amenity_name, sub_amenity=sub_amenity_name)
        return amenity_obj

    for amenity_name, sub_amenity_names in single_family_home.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='single_family_home')

    for amenity_name, sub_amenity_names in multi_family.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='multi_family')

    for amenity_name, sub_amenity_names in apartment_unit.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='apartment_unit')

    for amenity_name, sub_amenity_names in senior_living.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='senior_living')

    for amenity_name, sub_amenity_names in student_housing.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='student_housing')

    for amenity_name, sub_amenity_names in multi_family_unit.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the multi_family_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='multi_family_unit')

    for amenity_name, sub_amenity_names in senior_living_unit.items():
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='senior_living_unit')

    for amenity_name, sub_amenity_names in apartment_unit_unit.items():
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='apartment_unit_unit')

    for amenity_name, sub_amenity_names in student_housing_unit.items():
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='student_housing_unit')


class Migration(migrations.Migration):
    dependencies = [
        ('property_management', '0009_propertyassignedamenities_unit'),
    ]

    operations = [
        migrations.RunPython(add_amenities_and_property_types),
    ]
