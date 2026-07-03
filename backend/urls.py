from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .health_views import health_check, readiness_check
from centralized_patient_views import get_centralized_patient_urls

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
    path('api/dermatology/', include('dermatology.urls')),
    path('api/pathology/', include('pathology.urls')),
    path('api/cosmetology/', include('cosmetology.urls')),
    path('api/allopathy/', include('allopathy.urls')),
    path('homeopathy/', include('homeopathy.urls')),
    path('api/secureneat/', include('secureneat.urls')),
    path('api/secure-s3/', include('secureneat.secure_s3_urls')),
    path('api/usage/', include('usage_tracking.urls')),
    path('api/', include(get_centralized_patient_urls())),
    path('patients/', include('patients.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('dna-sequencing/', include('dna_sequencing.urls')),
]
