from django.contrib.auth import get_user_model

from common.utils import get_presigned_url
from apps.properties.infrastructure.models import ListingInfo, RentDetails, PropertyAssignedAmenities, Property, CostFeesCategory, OwnerInfo, CostFee, Unit, PropertyDocument
from apps.user_authentication.infrastructure.models import PropertyOwner # why is a model from other app being used here 

from .rent_details_retrieve import RentDetailsRetrieveSerializer
from .listing_info_retrieve import ListingInfoRetrieveSerializer
from .cost_fee_retrieve import CostFeeRetrieveSerializer
from .owner_info_retrieve import OwnerInfoRetrieveSerializer
from .document_retrieve import DocumentRetrieveSerializer

#  this doesnt look a a proper serializer, look into it
class PropertySummaryRetrieveSerializer:
    @staticmethod
    def get_amenities(property_id, unit_id):
        sub_amenities = PropertyAssignedAmenities.objects.filter(property=property_id, unit=unit_id).select_related(
            'sub_amenity')
        model = Property
        if unit_id:
            model = Unit
            instance_id = unit_id
        else:
            instance_id = property_id
        other_amenities = model.objects.filter(id=instance_id).values_list('other_amenities', flat=True)
        amenities_data = dict()
        for amenity in sub_amenities:
            a_name = amenity.sub_amenity.amenity
            if a_name not in amenities_data:
                amenities_data[a_name] = list()
            amenities_data[a_name].append({
                'id': amenity.sub_amenity.id,
                'name': amenity.sub_amenity.sub_amenity
            })
        amenities_data['other_amenities'] = list(other_amenities)
        return amenities_data

    @staticmethod
    def get_rental_details(property_id, unit_id):
        rental_details_instance = RentDetails.objects.filter(property=property_id, unit=unit_id).first()
        return RentDetailsRetrieveSerializer(rental_details_instance).data if rental_details_instance else None

    @staticmethod
    def get_listing_info(property_id):
        listing_info_instance = ListingInfo.objects.filter(property=property_id).first()
        return ListingInfoRetrieveSerializer(listing_info_instance).data if listing_info_instance else None

    @staticmethod
    def get_cost_fees(property_id, unit_id):
        cost_fee_data = []
        cost_category_instances = CostFeesCategory.objects.filter(property=property_id, unit=unit_id)
        for cost_fee in cost_category_instances:
            cost_fee_obj = {
                'category_name': cost_fee.category_name,
                'fees': [CostFeeRetrieveSerializer(f).data for f in CostFee.objects.filter(category=cost_fee.id)]
            }
            cost_fee_data.append(cost_fee_obj)
        return cost_fee_data

    @staticmethod
    def get_owners(property_id):
        owners_data = OwnerInfo.objects.filter(property=property_id)
        owners = list()
        for owner in owners_data:
            data = OwnerInfoRetrieveSerializer(owner).data
            try:
                get_user = get_user_model().objects.get(email=data.get('email'), is_active=True)
                data['username'] = get_user.first_name + ' ' + get_user.last_name
                data['phone_number'] = get_user.phone_number
                try:
                    profile = PropertyOwner.objects.filter(user_id=get_user.id).values_list('profile_image_path', flat=True).first()
                    if profile:
                        data['profile_image_path'] = get_presigned_url(profile)
                    else:
                        data['profile_image_path'] = None
                except PropertyOwner.DoesNotExist:
                    data['profile_image_path'] = None
            except get_user_model().DoesNotExist:
                data['username'] = None
                data['phone_number'] = None
                data['profile_image_path'] = None
            owners.append(data)
        return owners

    @staticmethod
    def get_documents(property_id, unit_id):
        document_instances = PropertyDocument.objects.filter(property=property_id, unit=unit_id)
        return [DocumentRetrieveSerializer(document).data for document in document_instances]