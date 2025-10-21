from apps.property_management.infrastructure.models import ListingInfo, PropertyPhoto


# trash this file if unused
class ListingInfoService:
    # This method was decoupled from listing info serializer and was unused there as well - check if safe to remove
    @staticmethod
    def create_listing_info(validated_data, photos, page_saved):
        listing_info = ListingInfo.objects.create(**validated_data)

        for photo in photos:
            PropertyPhoto.objects.create(property=listing_info.property, photo=photo)

        property_obj = listing_info.property
        property_obj.page_saved = page_saved
        property_obj.save(update_fields=['page_saved'])

        return listing_info
