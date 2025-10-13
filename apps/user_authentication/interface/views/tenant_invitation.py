from datetime import timedelta

from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.filters import OrderingFilter

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from apps.properties.filters import CustomSearchFilter

from common.constants import Success, Error
from common.utils import CustomResponse, get_presigned_url, send_email_

from apps.properties.infrastructure.models import Property, Unit
from apps.user_authentication.infrastructure.models import Agreements, Tenant, TenantInvitation
from apps.user_authentication.interface.serializers import TenantInvitationSerializer, InvitationAgreementSerializer
from apps.user_authentication.application.pagination import TenantInvitationPagination


class TenantInvitationView(APIView):
    """
    API view to send tenant invitations.
    Accepts first_name, last_name, email, assignment_type, assignment_id, tenant_type, lease details in the payload.
    Supports search functionality for tenant name, email, and tenant_type.
    """
    queryset = TenantInvitation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TenantInvitationSerializer
    filter_backends = [DjangoFilterBackend, CustomSearchFilter, OrderingFilter]
    filterset_fields = ['tenant_type', 'accepted', 'blocked', 'assignment_type', 'assignment_id']
    search_fields = ['first_name', 'last_name', 'email', 'tenant_type']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        return self.queryset.filter(sender=self.request.user).order_by('-created_at')

    def filter_queryset(self, queryset):
        """Apply filters to queryset"""
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def post(self, request):
        """
        Send tenant invitation email and save invitation record.

        Expected payload:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "assignment_type": "unit",  # or "property"
            "assignment_id": 1,
            "tenant_type": "individual",
            "lease_amount": 2000,
            "security_deposit": 4000,
            "lease_start_date": "2025-02-01",
            "lease_end_date": "2026-02-01",
            "lease_agreement": <file>
        }
        """
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email')
        tenant_type = request.data.get('tenant_type')
        assignment_type = request.data.get('assignment_type')
        assignment_id = request.data.get('assignment_id')
        tenant_type_display = dict(TenantInvitation.TENANT_TYPE_CHOICES).get(tenant_type, tenant_type)

        # Check if tenant already exists
        if Tenant.objects.filter(user_id__email=email).exists():
            return CustomResponse({"error": Error.TENANT_ALREADY_EXISTS}, status=status.HTTP_400_BAD_REQUEST)

        # Validate assignment exists and belongs to user
        if assignment_type == 'property':
            try:
                assigned_obj = Property.objects.get(id=assignment_id, property_owner=request.user)
                assignment_name = assigned_obj.name
                if assigned_obj.status == 'occupied':
                    return CustomResponse({"error": Error.PROPERTY_OCCUPIED}, status=status.HTTP_400_BAD_REQUEST)
            except Property.DoesNotExist:
                return CustomResponse({"error": Error.PROPERTY_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        elif assignment_type == 'unit':
            try:
                assigned_obj = Unit.objects.get(id=assignment_id, property__property_owner=request.user)
                assignment_name = f"{assigned_obj.number} - {assigned_obj.property.name}"
                if assigned_obj.status == 'occupied':
                    return CustomResponse({"error": Error.UNIT_OCCUPIED}, status=status.HTTP_400_BAD_REQUEST)
            except Unit.DoesNotExist:
                return CustomResponse({"error": Error.UNIT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        else:
            return CustomResponse({"error": "assignment_type must be either 'unit' or 'property'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing invitations and clean up expired ones
        existing_invitation = TenantInvitation.objects.filter(
            email=email, sender=request.user, tenant_type=tenant_type,
            assignment_type=assignment_type, assignment_id=assignment_id
        ).first()

        if existing_invitation:
            if existing_invitation.expired_at <= timezone.now() and not existing_invitation.accepted:
                # Delete expired invitation
                existing_invitation.delete()
            elif existing_invitation.accepted:
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_ALREADY_ACCEPTED.format(email, tenant_type_display, assignment_name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Clean up expired invitations for same email+tenant_type+sender+assignment
                TenantInvitation.objects.filter(
                    email=email,
                    sender=request.user,
                    tenant_type=tenant_type,
                    assignment_type=assignment_type,
                    assignment_id=assignment_id,
                    expired_at__lte=timezone.now(),
                    accepted=False
                ).delete()

        if not serializer.is_valid():
            if 'must make a unique set' in str(serializer.errors):
                return CustomResponse(
                    {"error": Error.TENANT_INVITATION_ALREADY_SENT.format(email, tenant_type_display, assignment_name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        email = validated_data['email']
        tenant_type = validated_data['tenant_type']
        assignment_type = validated_data['assignment_type']
        assignment_id = validated_data['assignment_id']
        lease_amount = validated_data['lease_amount']
        security_deposit = validated_data.get('security_deposit', 0)
        lease_start_date = validated_data['lease_start_date']
        lease_end_date = validated_data['lease_end_date']
        lease_agreement = validated_data.get('lease_agreement')

        try:
            # Get owner name for email
            owner_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if not owner_name:
                owner_name = request.user.email

            with transaction.atomic():
                invitation = TenantInvitation.objects.create(
                    sender=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    assignment_type=assignment_type,
                    assignment_id=assignment_id,
                    tenant_type=tenant_type,
                    lease_amount=lease_amount,
                    security_deposit=security_deposit,
                    lease_start_date=lease_start_date,
                    lease_end_date=lease_end_date,
                    expired_at=timezone.now() + timedelta(days=5)
                )

                agreement = Agreements.objects.create(
                    invitation=invitation,
                    lease_agreement=lease_agreement
                )

            email_variables = {
                'TENANT_FIRST_NAME': first_name,
                'OWNER_NAME': owner_name,
                'SETUP_LINK': f"{settings.FRONTEND_DOMAIN}/auth/signup?tenant=true&invitation_id={invitation.id}"
            }

            send_email_(email, email_variables, 'INVITE-TENANT')

            response_data = {
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'tenant_type': invitation.tenant_type,
                'assignment_type': invitation.assignment_type,
                'assignment_id': invitation.assignment_id,
                'assignment_name': assignment_name,
                'lease_amount': invitation.lease_amount,
                'security_deposit': invitation.security_deposit,
                'lease_agreement_url': get_presigned_url(agreement.lease_agreement.name) if agreement.lease_agreement else None,
                'lease_start_date': invitation.lease_start_date,
                'lease_end_date': invitation.lease_end_date,
                'lease_ended': True if invitation.lease_end_date <= timezone.now().date() else False,
                'created_at': invitation.created_at
            }

            return CustomResponse(
                {
                    "message": Success.TENANT_INVITATION_SENT,
                    "data": response_data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return CustomResponse(
                {"error": Error.TENANT_INVITATION_SEND_FAILED.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Get list of tenant invitations with pagination and filtering"""
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        paginator = TenantInvitationPagination()
        result_page = paginator.paginate_queryset(filtered_queryset, request)

        invitation_data = []
        for invitation in result_page:
            # Get assignment name based on type
            assigned_obj = invitation.assigned_object
            assignment_name = ""
            if assigned_obj:
                if invitation.assignment_type == 'property':
                    assignment_name = assigned_obj.name
                elif invitation.assignment_type == 'unit':
                    assignment_name = f"{assigned_obj.number} - {assigned_obj.property.name}"

            invitation_data.append({
                'id': invitation.id,
                'first_name': invitation.first_name,
                'last_name': invitation.last_name,
                'email': invitation.email,
                'tenant_type': invitation.tenant_type,
                'tenant_type_display': dict(TenantInvitation.TENANT_TYPE_CHOICES).get(invitation.tenant_type, invitation.tenant_type),
                'assignment_type': invitation.assignment_type,
                'assignment_id': invitation.assignment_id,
                'assignment_name': assignment_name,
                'lease_amount': invitation.lease_amount,
                'security_deposit': invitation.security_deposit,
                'lease_start_date': invitation.lease_start_date,
                'lease_end_date': invitation.lease_end_date,
                'lease_ended': True if invitation.lease_end_date <= timezone.now().date() else False,
                'accepted': invitation.accepted,
                'blocked': invitation.blocked,
                'created_at': invitation.created_at
            })

        return paginator.get_paginated_response(invitation_data)

    def put(self, request):
        """
        Update invitation agreement status and signed agreement file.
        Expected payload:
        - invitation_id (integer): The invitation ID to update
        - agreed (boolean): Must be true to update agreement
        - signed_agreement (file): The signed agreement file
        """
        serializer = InvitationAgreementSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        agreed = validated_data.get('agreed')
        invitation_id = validated_data.get('invitation_id')
        signed_agreement = validated_data.get('signed_agreement')

        try:
            invitation = TenantInvitation.objects.get(id=invitation_id)
        except TenantInvitation.DoesNotExist:
            return CustomResponse(
                {"error": Error.INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            agreement = Agreements.objects.get(invitation=invitation_id)
        except Agreements.DoesNotExist:
            return CustomResponse(
                {"error": Error.AGREEMENT_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.expired_at and invitation.expired_at < timezone.now():
            return CustomResponse(
                {"error": Error.INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            invitation.agreed = agreed
            agreement.signed_agreement = signed_agreement
            invitation.save(update_fields=['agreed', 'updated_at'])
            agreement.save(update_fields=['signed_agreement'])
        return CustomResponse({"message": Success.INVITATION_AGREEMENT_UPDATED}, status=status.HTTP_200_OK)
