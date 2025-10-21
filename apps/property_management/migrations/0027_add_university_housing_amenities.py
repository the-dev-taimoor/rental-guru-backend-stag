from django.db import migrations


def add_amenities_and_property_types(apps, schema_editor):
    Amenities = apps.get_model('property_management', 'Amenities')
    PropertyTypeAndAmenity = apps.get_model('property_management', 'PropertyTypeAndAmenity')

    university_housing = {
        "Laundry Facilities": ["Shared laundry room in the building", "Shared washer-dryer hookups per floor", "No laundry facilities"],
        "Student Living Features": [
            "Shared Study Lounge",
            "Quiet Study Pods",
            "High-Speed Wi-Fi in Common Areas",
            "Library Access",
            "Computer Lab Room",
        ],
        "Building Amenities": [
            "Cafeteria or Dining Hall",
            "Gym or Fitness Area",
            "Recreation/Game Room",
            "Vending Machines",
            "24/7 Security Desk",
            "Surveillance Cameras (CCTV)",
            "Mailroom or Package Locker",
        ],
        "Accessibility Features": ["Wheelchair Access", "Elevator Access", "Ramp Entry", "Braille Signage", "Ground-Level Entry"],
        "Parking Options": ["Bicycle Parking", "Student Vehicle Parking Lot", "Staff-Only Parking", "No Onsite Parking"],
    }

    university_housing_unit = {
        "Comfort & Privacy": ["Study Desk", "Personal Wardrobe", "Single Bed", "Attached Bathroom", "Mini-Fridge"],
        "Technology & Utilities": ["Wi-Fi Access", "Room Heater", "Personal Power Outlets", "Smart Lock / Keycard Entry"],
        "Safety & Accessibility": ["Fire Alarm", "Smoke Detector", "Emergency Exit Nearby", "Room Accessible to Disabled"],
        "Add-ons": ["Air Conditioning", "Personal Microwave", "TV in Room"],
    }

    # Function to create or get an existing amenity and sub-amenity
    def get_or_create_amenity(amenity_name, sub_amenity_name):
        # Check if the amenity already exists
        amenity_obj, created = Amenities.objects.get_or_create(amenity=amenity_name, sub_amenity=sub_amenity_name)
        return amenity_obj

    for amenity_name, sub_amenity_names in university_housing.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the university_housing property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='university_housing')

    for amenity_name, sub_amenity_names in university_housing_unit.items():
        # For each amenity, check if it exists and get its reference
        for sub_amenity_name in sub_amenity_names:
            amenity_obj = get_or_create_amenity(amenity_name, sub_amenity_name)
            # Create the PropertyTypeAndAmenity record for the university_housing_unit property type
            PropertyTypeAndAmenity.objects.get_or_create(sub_amenities=amenity_obj, property_type='university_housing_unit')


class Migration(migrations.Migration):
    dependencies = [
        ('property_management', '0026_listinginfo_occupancy_type_and_more'),
    ]

    operations = [
        migrations.RunPython(add_amenities_and_property_types),
    ]
