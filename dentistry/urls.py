from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet, DentistViewSet, AppointmentViewSet, TreatmentViewSet,
    DentalAIAnalysisViewSet, DentalEmergencyViewSet, TreatmentPlanViewSet,
    DashboardViewSet, CancerDetectionViewSet, CancerDetectionImageViewSet,
    CancerRiskAssessmentViewSet, CancerTreatmentPlanViewSet, CancerNotificationViewSet,
    # S3 Data Management Views
    DentistryInstitutionViewSet, DentistryPatientViewSet, DentistryFileViewSet,
    DentistryAnalysisViewSet, DentistryS3ManagementViewSet
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'dentists', DentistViewSet, basename='dentist')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'treatments', TreatmentViewSet, basename='treatment')
router.register(r'ai-analyses', DentalAIAnalysisViewSet, basename='ai-analysis')
router.register(r'emergencies', DentalEmergencyViewSet, basename='emergency')
router.register(r'treatment-plans', TreatmentPlanViewSet, basename='treatment-plan')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Cancer Detection Endpoints
router.register(r'cancer-detections', CancerDetectionViewSet, basename='cancer-detection')
router.register(r'cancer-detection-images', CancerDetectionImageViewSet, basename='cancer-detection-image')
router.register(r'cancer-risk-assessments', CancerRiskAssessmentViewSet, basename='cancer-risk-assessment')
router.register(r'cancer-treatment-plans', CancerTreatmentPlanViewSet, basename='cancer-treatment-plan')
router.register(r'cancer-notifications', CancerNotificationViewSet, basename='cancer-notification')

# S3 Data Management Endpoints
router.register(r'institutions', DentistryInstitutionViewSet, basename='institution')
router.register(r's3-patients', DentistryPatientViewSet, basename='s3-patient')
router.register(r'files', DentistryFileViewSet, basename='file')
router.register(r'analyses', DentistryAnalysisViewSet, basename='analysis')
router.register(r's3', DentistryS3ManagementViewSet, basename='s3-management')

app_name = 'dentistry'

urlpatterns = [
    path('', include(router.urls)),
]
