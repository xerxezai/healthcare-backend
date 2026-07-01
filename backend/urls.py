from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .health_views import health_check, readiness_check

def root_health_check(request):
    return HttpResponse("Healthcare Backend OK")

urlpatterns = [
    path('', root_health_check),
    path('health/', health_check, name='health_check'),
    path('ready/', readiness_check, name='readiness_check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('hospital.auth_urls')),
    path('api/hospital/', include('hospital.urls')),
    path('api/medicine/', include('medicine.urls')),
    path('api/radiology/', include('radiology.urls')),
    path('api/dentistry/', include('dentistry.urls')),
    path('patients/', include('patients.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('dna-sequencing/', include('dna_sequencing.urls')),
]
