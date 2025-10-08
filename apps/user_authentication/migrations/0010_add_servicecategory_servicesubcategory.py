from django.db import migrations

def add_service_categories_and_subcategories(apps, schema_editor):
    Category = apps.get_model('user_authentication', 'ServiceCategory')
    Subcategory = apps.get_model('user_authentication', 'ServiceSubCategory')

    categories_with_subcategories = {
        "General Maintenance": [
            "Basic Repairs",
            "Fixture Replacement",
            "Preventive Maintenance",
            "Wall Patching",
            "Furniture Assembly",
            "Minor Plumbing Fixes",
            "Minor Electrical Fixes",
            "Appliance Troubleshooting",
            "Window & Door Adjustment",
            "General Handyman Tasks"
        ],
        "Renovation & Remodeling": [
            "Kitchen Remodeling",
            "Bathroom Remodeling",
            "Basement Finishing",
            "Room Additions",
            "Floor Plan Reconfiguration",
            "Drywall Installation",
            "Ceiling Work",
            "Cabinet Installation",
            "Full Home Renovation",
            "Interior Design Integration"
        ],
        "Plumbing": [
            "Leak Repair",
            "Pipe Installation",
            "Drain Cleaning",
            "Water Heater Repair/Installation",
            "Faucet and Fixture Installation",
            "Sewer Line Repair",
            "Toilet Repair/Installation",
            "Sump Pump Installation",
            "Gas Line Repair/Installation",
            "Emergency Plumbing Services"
        ],
        "Electrical": [
            "Wiring & Rewiring",
            "Switch & Outlet Installation",
            "Circuit Breaker Repair",
            "Light Fixture Installation",
            "Ceiling Fan Installation",
            "Fuse Box Upgrades",
            "Surge Protection",
            "Electrical Safety Inspection",
            "Smart Home Device Setup",
            "Emergency Electrical Services"
        ],
        "HVAC": [
            "Air Conditioning Repair/Installation",
            "Heating System Repair/Installation",
            "Ventilation System Cleaning",
            "Ductwork Repair/Installation",
            "Thermostat Installation",
            "HVAC Maintenance Contracts",
            "Air Quality Testing",
            "Emergency HVAC Services",
            "Boiler Repair/Installation",
            "Heat Pump Repair/Installation"
        ],
        "Cleaning & Janitorial": [
            "Residential Cleaning",
            "Commercial Cleaning",
            "Post-Construction Cleaning",
            "Deep Cleaning",
            "Move-In/Move-Out Cleaning",
            "Window Cleaning",
            "Carpet Cleaning",
            "Sanitization & Disinfection",
            "Trash Removal",
            "Restroom Cleaning"
        ],
        "Carpentry": [
            "Framing",
            "Door & Window Installation",
            "Staircase Building",
            "Custom Shelving",
            "Wood Trim & Molding",
            "Deck Construction/Repair",
            "Cabinetry",
            "Wood Repair",
            "Partitions & Paneling",
            "Finish Carpentry"
        ],
        "Painting": [
            "Interior Painting",
            "Exterior Painting",
            "Wallpaper Removal",
            "Staining & Varnishing",
            "Ceiling Painting",
            "Touch-Ups",
            "Paint Color Consultation",
            "Fence & Gate Painting",
            "Spray Painting",
            "Drywall Patching & Painting"
        ],
        "Flooring": [
            "Tile Installation",
            "Hardwood Flooring",
            "Laminate Flooring",
            "Vinyl Flooring",
            "Carpet Installation",
            "Floor Repair",
            "Grouting Services",
            "Floor Leveling",
            "Baseboard Installation",
            "Epoxy Flooring"
        ],
        "Masonry & Tiling": [
            "Brickwork",
            "Stone Masonry",
            "Tile Setting",
            "Concrete Repair",
            "Fireplace Construction",
            "Patio Installation",
            "Chimney Repair",
            "Retaining Wall Construction",
            "Facade Restoration",
            "Grout Cleaning & Sealing"
        ],
        "Windows & Doors": [
            "Window Installation",
            "Door Installation",
            "Window Repair",
            "Door Repair",
            "Glass Replacement",
            "Sliding Door Repair",
            "Screen Repair",
            "Security Door Setup",
            "Weatherproofing",
            "Lock Installation"
        ],
        "Landscaping & Outdoor Services": [
            "Lawn Mowing",
            "Tree Trimming",
            "Irrigation System Setup",
            "Garden Design",
            "Fencing Installation",
            "Deck & Patio Maintenance",
            "Snow Removal",
            "Outdoor Lighting",
            "Pest-Repellent Landscaping",
            "Mulching & Weeding"
        ],
        "Security & Access Systems": [
            "CCTV Installation",
            "Burglar Alarm Setup",
            "Access Control Systems",
            "Intercom System Installation",
            "Smart Lock Installation",
            "Security System Maintenance",
            "Door Entry Systems",
            "Fire Alarm Installation",
            "24/7 Monitoring Setup",
            "Motion Sensor Setup"
        ],
        "Appliance Repair & Installation": [
            "Refrigerator Repair",
            "Washing Machine Repair",
            "Dishwasher Installation",
            "Dryer Repair",
            "Microwave Repair",
            "Oven & Stove Installation",
            "Water Filter Installation",
            "Garbage Disposal Fixes",
            "AC Unit Setup",
            "Cooktop Repair"
        ],
        "Pest Control": [
            "Rodent Control",
            "Termite Treatment",
            "Cockroach Elimination",
            "Bed Bug Treatment",
            "Mosquito Control",
            "Ant Infestation Solutions",
            "Bird Control",
            "Fumigation",
            "Eco-Friendly Pest Control",
            "Pest Prevention Consultation"
        ],
        "Moving & Junk Removal": [
            "Home Moving",
            "Office Relocation",
            "Furniture Disassembly/Reassembly",
            "Packing & Unpacking",
            "Appliance Moving",
            "Heavy Item Hauling",
            "Junk Removal",
            "Donation Pickups",
            "Garage Cleanouts",
            "Storage Organization"
        ],
        "Roofing & Waterproofing": [
            "Roof Inspection",
            "Roof Leak Repair",
            "Shingle Replacement",
            "Flat Roof Installation",
            "Waterproof Membrane Setup",
            "Gutter Cleaning",
            "Downspout Installation",
            "Roof Coating",
            "Emergency Roof Repair",
            "Basement Waterproofing"
        ],
        "Glass & Mirror Work": [
            "Window Glass Replacement",
            "Custom Mirror Installation",
            "Shower Glass Enclosure Setup",
            "Glass Partition Installation",
            "Glass Door Repair",
            "Tabletop Glass",
            "Decorative Glass Work",
            "Tempered Glass Replacement",
            "Sliding Glass Doors",
            "Display Case Setup"
        ],
        "Handyman Services": [
            "TV Mounting",
            "Picture Hanging",
            "Shelving Installation",
            "Furniture Assembly",
            "Minor Repairs",
            "Door Adjustments",
            "Blind & Curtain Installation",
            "Mailbox Repair",
            "Garage Organization",
            "General Maintenance Help"
        ],
    }

    for category_name, subcategories in categories_with_subcategories.items():
        category_obj = Category.objects.create(name=category_name)
        for subcat_name in subcategories:
            Subcategory.objects.create(category_id=category_obj, name=subcat_name)


class Migration(migrations.Migration):

    dependencies = [
        ('user_authentication', '0009_servicecategory_servicesubcategory'),
    ]

    operations = [
        migrations.RunPython(add_service_categories_and_subcategories),
    ]
