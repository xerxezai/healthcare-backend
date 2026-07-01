"""
Health check views for Railway deployment
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
import time

@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Railway health check endpoint
    Returns system status and database connectivity
    """
    start_time = time.time()
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    health_data = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": int(time.time()),
        "database": db_status,
        "response_time_ms": response_time,
        "service": "Healthcare Management Backend",
        "version": "1.0.0"
    }
    
    status_code = 200 if db_status == "connected" else 503
    return JsonResponse(health_data, status=status_code)

@never_cache  
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Kubernetes/Railway readiness probe
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
            
        return JsonResponse({
            "ready": True,
            "migrations_applied": migration_count,
            "timestamp": int(time.time())
        })
    except Exception as e:
        return JsonResponse({
            "ready": False,
            "error": str(e),
            "timestamp": int(time.time())
        }, status=503)