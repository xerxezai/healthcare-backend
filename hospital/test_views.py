from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def test_endpoint(request):
    """Simple test endpoint to verify API connectivity"""
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'message': 'Test endpoint is working',
            'method': 'GET'
        })
    elif request.method == 'POST':
        try:
            body = json.loads(request.body) if request.body else {}
            return JsonResponse({
                'status': 'success',
                'message': 'POST request received',
                'data': body,
                'method': 'POST'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON',
                'method': 'POST'
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': f'Method {request.method} not allowed'
        })
