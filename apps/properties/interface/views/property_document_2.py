import json

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.properties.application.pagination import DocumentsPagination
from apps.properties.infrastructure.filters import DocumentFilter
from apps.properties.infrastructure.models import Property, PropertyDocument, Unit
from apps.properties.interface.serializers import DocumentCreateSerializer, DocumentRetrieveSerializer, UploadDocumentFormSerializer
from common.constants import Error, Success
from common.utils import CustomResponse


class PropertyDocumentViewSet2(APIView):
    serializer_class = DocumentCreateSerializer
    pagination_class = DocumentsPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = DocumentFilter
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    @staticmethod
    def check_document_types(property_id, unit_id, data):
        document_types = [item['document_type'] for item in data]
        document_types_to_check = [doc_type for doc_type in document_types if doc_type != 'other']
        existing_documents = PropertyDocument.objects.filter(
            Q(property_id=property_id) & Q(unit_id=unit_id) & Q(document_type__in=document_types_to_check)
        )
        if existing_documents.exists():
            raise ValidationError(Error.DOCUMENT_TYPE_EXISTS_V2.format(', '.join([e.document_type for e in existing_documents])))

    def post(self, request):
        existing_data = request.data.get('existing_data')
        data_to_update = []
        if request.data.get('existing_data'):
            data_to_update = json.loads(existing_data).get('data') if existing_data else []
        updated_call = False
        serializer = UploadDocumentFormSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return CustomResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        property_id = serializer.validated_data['property']
        unit_id = serializer.validated_data.get('unit')
        page_saved = serializer.validated_data['page_saved']
        data = serializer.validated_data['data']['data']

        obj = get_object_or_404(Property, id=property_id)

        # self.check_document_types(property_id, unit_id, data)

        if data_to_update:
            self.check_document_exists_update_case(data_to_update, property_id=obj.id, unit_id=unit_id)
        self.check_document_exists_create_case(data, property_id=obj.id, unit_id=unit_id)

        saved_documents = []
        # for new documents
        if data:
            documents = serializer.validated_data.get('documents')
            if not documents:
                return CustomResponse({"error": Error.DOCUMENTS_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
            if len(data) != len(documents):
                return CustomResponse({"error": Error.DOCUMENT_DETAIL_MISSING}, status=status.HTTP_400_BAD_REQUEST)

            for index, item in enumerate(data):
                document_data = item
                document_file = documents[index]
                self.create_document(document_data, document_file, saved_documents, property_id, unit_id)
        # for existing documents to edit
        if data_to_update:
            for docs in data_to_update:
                document_data = docs
                if document_data.get('id'):
                    self.update_document(document_data, saved_documents)
                    updated_call = True

            if unit_id:
                obj = get_object_or_404(Unit, id=unit_id)

            if not updated_call:
                obj.page_saved = page_saved
                obj.save(update_fields=['page_saved'])

        return CustomResponse({"data": saved_documents}, status=status.HTTP_201_CREATED)

    def check_document_exists_update_case(self, data, property_id, unit_id):
        existing_docs_ids = [d.get('id') for d in data if d.get('id')]
        existing_docs = PropertyDocument.objects.filter(id__in=existing_docs_ids, property=property_id, unit=unit_id)

        # Check if all IDs from payload exist in database
        db_doc_ids = set(existing_docs.values_list('id', flat=True))
        missing_ids = set(existing_docs_ids) - db_doc_ids

        if missing_ids:
            raise ValidationError(Error.DOC_ID_NOT_FOUND.format(', '.join(map(str, missing_ids))))

    def check_document_exists_create_case(self, data, property_id, unit_id):
        document_types = [item['document_type'] for item in data if not item.get('id')]
        document_types_to_check = [doc_type for doc_type in document_types if doc_type != 'other']
        existing_documents = PropertyDocument.objects.filter(
            Q(property_id=property_id) & Q(unit_id=unit_id) & Q(document_type__in=document_types_to_check)
        )
        if existing_documents.exists():
            raise ValidationError(Error.DOCUMENT_TYPE_EXISTS_V2.format(', '.join([e.document_type for e in existing_documents])))

    def update_document(self, document_data, saved_documents):
        property_document = PropertyDocument.objects.get(id=document_data.get('id'))
        # property_document.document = document_file
        property_document.title = document_data.get('title') if document_data.get('title') else property_document.title
        property_document.visibility = document_data.get('visibility') if document_data.get('visibility') else property_document.visibility
        property_document.save()
        property_document_serialized = DocumentRetrieveSerializer(property_document)
        saved_documents.append(property_document_serialized.data)

    def create_document(self, document_data, document_file, saved_documents, property_id, unit_id):
        req_data = {
            "unit": unit_id,
            "property": property_id,
            "document": document_file,
            "title": document_data.get('title'),
            "visibility": document_data.get('visibility'),
            "document_type": document_data.get('document_type'),
        }

        serializer = self.serializer_class(data=req_data)
        serializer.is_valid(raise_exception=True)

        property_document = PropertyDocument.objects.create(**serializer.validated_data)

        property_document_serialized = DocumentRetrieveSerializer(property_document)
        saved_documents.append(property_document_serialized.data)

    def delete(self, request, *args, **kwargs):
        document_id = kwargs.get('id')
        try:
            document = PropertyDocument.objects.get(id=document_id)
        except PropertyDocument.DoesNotExist:
            return CustomResponse({"error": Error.DOCUMENT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if document.property.property_owner != request.user:
            return CustomResponse({"error": Error.DOCUMENT_DELETE_PERMISSION}, status=status.HTTP_403_FORBIDDEN)

        document.delete()

        return CustomResponse({"message": Success.DOCUMENT_DELETED}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        property_id = request.query_params.get('property')
        if not property_id:
            raise ValidationError(Error.PROPERTY_ID_REQUIRED)
        unit_id = request.query_params.get('unit')

        queryset = PropertyDocument.objects.filter(property=property_id, unit=unit_id)

        filterset = self.filterset_class(request.query_params, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        paginator = self.pagination_class()

        if not queryset.exists():
            return CustomResponse({"message": Success.DOCUMENTS_LIST, 'data': []}, status=status.HTTP_200_OK)

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            return paginator.get_paginated_response(DocumentRetrieveSerializer(page, many=True).data)

        all_data = DocumentRetrieveSerializer(queryset, many=True).data
        return CustomResponse({"message": Success.DOCUMENTS_LIST, 'data': all_data}, status=status.HTTP_200_OK)
