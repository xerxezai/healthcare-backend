# AWS notification service status endpoint

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .aws_notification_service import get_aws_notification_service


@api_view(['GET'])
@permission_classes([IsAdminUser])
def aws_service_status(request):
    """
    Get AWS notification service status (admin only)
    """
    try:
        service = get_aws_notification_service()
        service_status = service.get_service_status()
        
        return Response({
            'aws_services': service_status,
            'timestamp': timezone.now().isoformat(),
            'message': 'AWS notification service status retrieved successfully'
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
