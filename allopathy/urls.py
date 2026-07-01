from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AllopathyHospitalViewSet,
    AllopathyPatientS3ViewSet,
    AllopathyFileViewSet,
    AllopathyAnalysisViewSet,
    AllopathyMedicalRecordViewSet,
    AllopathyTreatmentPlanViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'hospitals', AllopathyHospitalViewSet, basename='allopathy-hospitals')
router.register(r'patients', AllopathyPatientS3ViewSet, basename='allopathy-patients')
router.register(r'files', AllopathyFileViewSet, basename='allopathy-files')
router.register(r'analyses', AllopathyAnalysisViewSet, basename='allopathy-analyses')
router.register(r'medical-records', AllopathyMedicalRecordViewSet, basename='allopathy-medical-records')
router.register(r'treatment-plans', AllopathyTreatmentPlanViewSet, basename='allopathy-treatment-plans')

app_name = 'allopathy'

urlpatterns = [
    path('', include(router.urls)),
]

# Additional URL patterns for specific API endpoints
urlpatterns += [
    # Hospital-specific endpoints
    path('hospitals/<uuid:pk>/statistics/', 
         AllopathyHospitalViewSet.as_view({'get': 'statistics'}), 
         name='hospital-statistics'),
    
    # Patient-specific endpoints
    path('patients/<uuid:pk>/medical-summary/', 
         AllopathyPatientS3ViewSet.as_view({'get': 'medical_summary'}), 
         name='patient-medical-summary'),
    path('patients/<uuid:pk>/update-vital-signs/', 
         AllopathyPatientS3ViewSet.as_view({'patch': 'update_vital_signs'}), 
         name='patient-update-vital-signs'),
    
    # File-specific endpoints
    path('files/<uuid:pk>/generate-download-url/', 
         AllopathyFileViewSet.as_view({'post': 'generate_download_url'}), 
         name='file-generate-download-url'),
    path('files/storage-analytics/', 
         AllopathyFileViewSet.as_view({'get': 'storage_analytics'}), 
         name='file-storage-analytics'),
    
    # Analysis-specific endpoints
    path('analyses/<uuid:pk>/approve/', 
         AllopathyAnalysisViewSet.as_view({'post': 'approve_analysis'}), 
         name='analysis-approve'),
    path('analyses/batch-process/', 
         AllopathyAnalysisViewSet.as_view({'post': 'batch_process'}), 
         name='analysis-batch-process'),
    
    # Treatment plan-specific endpoints
    path('treatment-plans/<uuid:pk>/update-status/', 
         AllopathyTreatmentPlanViewSet.as_view({'patch': 'update_status'}), 
         name='treatment-plan-update-status'),
]
