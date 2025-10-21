from rest_framework.response import Response
from rest_framework.views import APIView

from apps.property_management.infrastructure.models.listing_info import ListingInfo
from apps.property_management.interface.serializers.listing_info import ListingInfoSerializer


class PublicListingAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        listings = ListingInfo.objects.all()
        serializer = ListingInfoSerializer(listings, many=True)
        return Response(serializer.data)
