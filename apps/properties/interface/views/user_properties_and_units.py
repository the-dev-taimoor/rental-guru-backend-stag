from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.properties.application.pagination import UserPropertiesAndUnitsPagination
from apps.properties.infrastructure.models import Property, Unit
from apps.properties.interface.serializers import UserPropertyUnitSerializer
from common.constants import Success
from common.filters import CustomSearchFilter
from common.utils import CustomResponse


class UserPropertiesAndUnitsView(APIView):
    """
    API view to get vacant properties and units for the authenticated user.
    For single family homes: returns vacant properties only
    For other property types: returns vacant units only
    Supports search functionality for property name, unit number, and type.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [CustomSearchFilter]
    search_fields = ['name', 'number', 'type']

    def get_queryset(self):
        """Get the base queryset of properties and units for the authenticated user"""
        user = self.request.user
        result_data = []

        properties = Property.objects.filter(property_owner=user)

        for property_instance in properties:
            if property_instance.property_type == 'single_family_home':
                if property_instance.status == 'vacant':
                    result_data.append({'id': property_instance.id, 'name': property_instance.name, 'type': 'property'})
            else:
                units = Unit.objects.filter(property=property_instance, status='vacant')
                for unit in units:
                    result_data.append({'id': unit.id, 'name': f"{unit.number} - {property_instance.name}", 'type': 'unit'})

        return result_data

    def filter_queryset(self, queryset):
        """Apply filters to queryset using filter_backends"""
        search_query = self.request.query_params.get('q', '').strip()

        if search_query:
            filtered_data = []
            search_lower = search_query.lower()

            for item in queryset:
                # Search in name and type fields (following search_fields pattern)
                if search_lower in item['name'].lower() or search_lower in item['type'].lower():
                    filtered_data.append(item)

            return filtered_data

        return queryset

    def get(self, request):
        """Get list of user properties and units with pagination and search"""
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)

        # Apply pagination
        paginator = UserPropertiesAndUnitsPagination()
        result_page = paginator.paginate_queryset(filtered_queryset, request)

        if result_page is not None:
            serializer = UserPropertyUnitSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination fails
        serializer = UserPropertyUnitSerializer(filtered_queryset, many=True)
        return CustomResponse({'data': serializer.data, 'message': Success.USER_PROPERTIES_AND_UNITS_LIST}, status=status.HTTP_200_OK)
