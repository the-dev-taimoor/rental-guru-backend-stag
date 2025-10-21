from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.user_management.application.pagination import KYCRequestsPagination
from apps.user_management.infrastructure.models import KYCRequest, Role
from apps.user_management.interface.serializers import KYCVerifySerializer
from common.constants import Error, Success
from common.utils import CustomResponse, get_presigned_url


class KYCView(APIView):
    """
    API view to view kyc requests by Super Admin only.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KYCVerifySerializer
    pagination_class = KYCRequestsPagination

    @swagger_auto_schema(
        operation_description="Get all KYC requests with search and filter functionality. "
        "Use search to filter with name and status to filter on the basis of status column in query params.",
        responses={
            200: "List of KYC requests with pagination, search, and filter options.",
            403: "Permission denied. Only super admins can access this endpoint.",
        },
    )
    def get(self, request, *args, **kwargs):
        basename = request.resolver_match.url_name

        if basename == 'kyc_stats':
            return self.get_stats(request)
        else:
            return self.get_list(request)

    def get_list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return CustomResponse(
                {'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False, 'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC},
                status=status.HTTP_403_FORBIDDEN,
            )

        search_query = request.query_params.get('search', None)
        status_filter = request.query_params.get('status', None)

        kyc_requests = KYCRequest.objects.all().select_related('user_id').order_by('-id')

        if search_query:
            kyc_requests = kyc_requests.filter(
                Q(user_id__first_name__icontains=search_query)
                | Q(user_id__last_name__icontains=search_query)
                | Q(user_id__email__icontains=search_query)
            )

        if status_filter:
            kyc_requests = kyc_requests.filter(status=status_filter)

        user_ids = kyc_requests.values_list('user_id', flat=True).distinct()

        roles = Role.objects.filter(user_id__in=user_ids).values('user_id', 'role')
        user_roles = {role['user_id']: role['role'] for role in roles}

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(kyc_requests, request)

        response_data = []
        for kyc in result_page:
            kyc_data = KYCVerifySerializer(kyc).data
            user_role = user_roles.get(kyc.user_id.id, 'Not assigned')
            user_data = {
                'kyc_id': kyc.id,
                'full_name': f'{kyc.user_id.first_name} {kyc.user_id.last_name}',
                'email': kyc.user_id.email,
                'status': kyc.status,
                'role': user_role,
                'registration_date': kyc.created_at.strftime('%Y-%m-%d'),
                'front_image': get_presigned_url(kyc.front_image.name),
                'back_image': get_presigned_url(kyc.back_image.name) if kyc.back_image else None,
            }
            kyc_data.update(user_data)
            response_data.append(kyc_data)

        return paginator.get_paginated_response(response_data)

    def get_stats(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return CustomResponse(
                {'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False, 'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC},
                status=status.HTTP_403_FORBIDDEN,
            )
        counts = KYCRequest.objects.aggregate(
            total_requests=Count('id'),
            total_pending=Count('id', filter=Q(status='pending')),
            total_approved=Count('id', filter=Q(status='approved')),
            total_rejected=Count('id', filter=Q(status='rejected')),
        )
        return CustomResponse({'data': counts, 'message': Success.KYC_STATS}, status=status.HTTP_200_OK)

    def send_kyc_response(self, user, kyc_request):
        subject = 'Rental Guru – KYC Feedback'
        html_message = f"""
                        <html>
                        <body>
                            <p>Hi {user.first_name},</p>
                            <p>This email is in response of your KYC request.</p>
                            <p>Your request is {kyc_request.status}.</p>
                            <p>Reason: {kyc_request.review_notes if kyc_request.review_notes else ''}</p>
                        </body>
                        </html>
                        """
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        try:
            send_mail(
                subject,
                '',
                from_email,
                recipient_list,
                fail_silently=False,
                html_message=html_message,
            )
        except Exception as e:
            return CustomResponse(
                {'error': e, 'success': False, 'message': Error.KYC_RESPONSE_EMAIL_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request):
        if not request.user.is_superuser:
            return CustomResponse(
                {'error': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC, 'success': False, 'message': Error.ONLY_SUPER_ADMINS_CAN_VIEW_KYC},
                status=status.HTTP_403_FORBIDDEN,
            )

        kyc_id = request.data.get('kyc_id')
        kyc_status = request.data.get('status')
        review_notes = request.data.get('review_notes')
        try:
            kyc_request = KYCRequest.objects.get(id=kyc_id)
        except KYCRequest.DoesNotExist:
            raise NotFound('KYC not found.')

        if kyc_status:
            if kyc_status not in ['approved', 'rejected']:
                return CustomResponse(
                    {'error': Error.KYC_STATUS_INVALID, 'success': False, 'message': Error.KYC_STATUS_INVALID},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            kyc_request.status = kyc_status
            kyc_request.reviewed_at = timezone.now()
        if review_notes:
            kyc_request.review_notes = review_notes
        kyc_request.save()

        self.send_kyc_response(kyc_request.user_id, kyc_request)
        return CustomResponse({'message': Success.KYC_REQUEST_UPDATED_EMAIL_SENT}, status=status.HTTP_200_OK)
