from django.db import migrations


def add_amenities_and_property_types(apps, schema_editor):
    Amenities = apps.get_model('property_management', 'Amenities')
    PropertyTypeAndAmenity = apps.get_model('property_management', 'PropertyTypeAndAmenity')

    # Define amenities and sub-amenities for each property type
    amenities_for_single_family_home = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared washer-dryer hookups in the building", "No laundry facilities"],
        "Cooling": ["Central", "Wall"],
        "Heating": ["Baseboard", "Forced air", "Wall"],
        "Appliances": ["Dishwasher", "Freezer", "Microwave", "Oven"],
        "Flooring": ["Carpet", "Hardwood", "Tile"],
        "Room Setup": ["Room has private bath"],
        "Parking": ["Attached Garage", "Detached Garage", "Off-street Parking"],
        "Accessibility": ["Wheelchair access", "Accessible bathroom facilities"],
    }

    amenities_for_multi_family = {
        "Laundry Facilities": ["Shared laundry in the building", "Shared washer-dryer hookups in the building", "No laundry facilities"],
        "Cooling": ["Central", "Window"],
        "Heating": ["Forced air", "Heat pump"],
        "Appliances": ["Dishwasher", "Freezer", "Microwave", "Oven"],
        "Flooring": ["Carpet", "Hardwood", "Tile"],
        "Room Setup": ["Room is furnished", "Shared space is furnished"],
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
        "Parking": ["Gated Parking", "Off-street Parking"],
        "Accessibility": ["Wheelchair access", "Ramps/elevators"],
    }

    # Add amenities and sub-amenities for single_family_home
    for amenity_name, sub_amenity_names in amenities_for_single_family_home.items():
        amenity_obj = Amenities.objects.create(
            amenity=amenity_name, sub_amenity=sub_amenity_names[0]
        )  # Just add the first sub-amenity for now
        for sub_name in sub_amenity_names:
            # For each sub-amenity, create a corresponding entry in the Amenities table
            sub_amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_name)
            # Create a PropertyTypeAndAmenity record for single_family_home
            PropertyTypeAndAmenity.objects.create(sub_amenities=sub_amenity_obj, property_type='single_family_home')

    # Add amenities and sub-amenities for multi_family
    for amenity_name, sub_amenity_names in amenities_for_multi_family.items():
        amenity_obj = Amenities.objects.create(
            amenity=amenity_name, sub_amenity=sub_amenity_names[0]
        )  # Just add the first sub-amenity for now
        for sub_name in sub_amenity_names:
            # For each sub-amenity, create a corresponding entry in the Amenities table
            sub_amenity_obj = Amenities.objects.create(amenity=amenity_name, sub_amenity=sub_name)
            # Create a PropertyTypeAndAmenity record for multi_family
            PropertyTypeAndAmenity.objects.create(sub_amenities=sub_amenity_obj, property_type='multi_family')


class Migration(migrations.Migration):
    dependencies = [
        ('property_management', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_amenities_and_property_types),
    ]
