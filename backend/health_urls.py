from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
import json

@require_GET
@csrf_exempt
def health_check(request):
    """
    Health check endpoint for deployment verification
    """
    try:
        return JsonResponse({
            'status': 'healthy',
            'message': 'Backend is running successfully',
            'timestamp': str(request.timestamp) if hasattr(request, 'timestamp') else None
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)