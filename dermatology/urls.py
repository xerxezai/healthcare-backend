from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DermatologyDepartmentViewSet, SkinConditionViewSet, PatientViewSet,
    DermatologyConsultationViewSet, DiagnosticProcedureViewSet,
    SkinPhotoViewSet, TreatmentPlanViewSet, TreatmentOutcomeViewSet,
    AIAnalysisViewSet, DermatologyDashboardViewSet
)
from .services.s3_api_views import DermatologyS3DataManagerViewSet
from .delete_patients_api import delete_all_patients

app_name = 'dermatology'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'departments', DermatologyDepartmentViewSet, basename='dermatology-department')
router.register(r'skin-conditions', SkinConditionViewSet, basename='skin-condition')
router.register(r'patients', PatientViewSet, basename='dermatology-patient')
router.register(r'consultations', DermatologyConsultationViewSet, basename='dermatology-consultation')
router.register(r'diagnostic-procedures', DiagnosticProcedureViewSet, basename='diagnostic-procedure')
router.register(r'skin-photos', SkinPhotoViewSet, basename='skin-photo')
router.register(r'treatment-plans', TreatmentPlanViewSet, basename='treatment-plan')
router.register(r'treatment-outcomes', TreatmentOutcomeViewSet, basename='treatment-outcome')
router.register(r'ai-analyses', AIAnalysisViewSet, basename='ai-analysis')
router.register(r'dashboard', DermatologyDashboardViewSet, basename='dermatology-dashboard')

# S3 Data Management Router
router.register(r's3-data-manager', DermatologyS3DataManagerViewSet, basename='dermatology-s3-manager')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('delete-all-patients/', delete_all_patients, name='delete-all-patients'),
]

# URL patterns for the dermatology module:
# 
# Departments:
# GET /dermatology/api/departments/ - List all departments
# POST /dermatology/api/departments/ - Create new department
# GET /dermatology/api/departments/{id}/ - Get department details
# PUT /dermatology/api/departments/{id}/ - Update department
# DELETE /dermatology/api/departments/{id}/ - Delete department
# GET /dermatology/api/departments/{id}/consultations/ - Get department consultations
# GET /dermatology/api/departments/{id}/statistics/ - Get department statistics
#
# Skin Conditions:
# GET /dermatology/api/skin-conditions/ - List all skin conditions
# POST /dermatology/api/skin-conditions/ - Create new condition
# GET /dermatology/api/skin-conditions/{id}/ - Get condition details
# PUT /dermatology/api/skin-conditions/{id}/ - Update condition
# DELETE /dermatology/api/skin-conditions/{id}/ - Delete condition
# GET /dermatology/api/skin-conditions/by_category/ - Get conditions by category
# GET /dermatology/api/skin-conditions/{id}/treatment_outcomes/ - Get treatment outcomes
#
# Patients:
# GET /dermatology/api/patients/ - List all patients
# POST /dermatology/api/patients/ - Create new patient
# GET /dermatology/api/patients/{id}/ - Get patient details
# PUT /dermatology/api/patients/{id}/ - Update patient
# DELETE /dermatology/api/patients/{id}/ - Delete patient
# GET /dermatology/api/patients/{id}/consultations/ - Get patient consultations
# GET /dermatology/api/patients/{id}/medical_history/ - Get patient medical history
#
# Consultations:
# GET /dermatology/api/consultations/ - List all consultations
# POST /dermatology/api/consultations/ - Create new consultation
# GET /dermatology/api/consultations/{id}/ - Get consultation details
# PUT /dermatology/api/consultations/{id}/ - Update consultation
# DELETE /dermatology/api/consultations/{id}/ - Delete consultation
# POST /dermatology/api/consultations/{id}/start_consultation/ - Start consultation
# POST /dermatology/api/consultations/{id}/complete_consultation/ - Complete consultation
# GET /dermatology/api/consultations/today_schedule/ - Get today's schedule
# GET /dermatology/api/consultations/upcoming/ - Get upcoming consultations
#
# Diagnostic Procedures:
# GET /dermatology/api/diagnostic-procedures/ - List all procedures
# POST /dermatology/api/diagnostic-procedures/ - Create new procedure
# GET /dermatology/api/diagnostic-procedures/{id}/ - Get procedure details
# PUT /dermatology/api/diagnostic-procedures/{id}/ - Update procedure
# DELETE /dermatology/api/diagnostic-procedures/{id}/ - Delete procedure
# GET /dermatology/api/diagnostic-procedures/by_type/ - Get procedures by type
# POST /dermatology/api/diagnostic-procedures/{id}/mark_completed/ - Mark procedure as completed
#
# Skin Photos:
# GET /dermatology/api/skin-photos/ - List all photos
# POST /dermatology/api/skin-photos/ - Upload new photo
# GET /dermatology/api/skin-photos/{id}/ - Get photo details
# PUT /dermatology/api/skin-photos/{id}/ - Update photo
# DELETE /dermatology/api/skin-photos/{id}/ - Delete photo
# POST /dermatology/api/skin-photos/{id}/request_ai_analysis/ - Request AI analysis
# GET /dermatology/api/skin-photos/by_patient/ - Get photos by patient
#
# Treatment Plans:
# GET /dermatology/api/treatment-plans/ - List all treatment plans
# POST /dermatology/api/treatment-plans/ - Create new treatment plan
# GET /dermatology/api/treatment-plans/{id}/ - Get treatment plan details
# PUT /dermatology/api/treatment-plans/{id}/ - Update treatment plan
# DELETE /dermatology/api/treatment-plans/{id}/ - Delete treatment plan
# POST /dermatology/api/treatment-plans/{id}/activate/ - Activate treatment plan
# POST /dermatology/api/treatment-plans/{id}/complete/ - Complete treatment plan
# GET /dermatology/api/treatment-plans/active_treatments/ - Get active treatments
#
# Treatment Outcomes:
# GET /dermatology/api/treatment-outcomes/ - List all outcomes
# POST /dermatology/api/treatment-outcomes/ - Create new outcome
# GET /dermatology/api/treatment-outcomes/{id}/ - Get outcome details
# PUT /dermatology/api/treatment-outcomes/{id}/ - Update outcome
# DELETE /dermatology/api/treatment-outcomes/{id}/ - Delete outcome
# GET /dermatology/api/treatment-outcomes/success_rates/ - Get success rates
#
# AI Analyses:
# GET /dermatology/api/ai-analyses/ - List all AI analyses
# POST /dermatology/api/ai-analyses/ - Create new analysis
# GET /dermatology/api/ai-analyses/{id}/ - Get analysis details
# PUT /dermatology/api/ai-analyses/{id}/ - Update analysis
# DELETE /dermatology/api/ai-analyses/{id}/ - Delete analysis
# POST /dermatology/api/ai-analyses/{id}/validate_analysis/ - Doctor validation
# GET /dermatology/api/ai-analyses/pending_validation/ - Get pending validations
# GET /dermatology/api/ai-analyses/high_risk/ - Get high-risk analyses
#
# Dashboard:
# GET /dermatology/api/dashboard/statistics/ - Get dashboard statistics
# GET /dermatology/api/dashboard/recent_activity/ - Get recent activity
# GET /dermatology/api/dashboard/alerts/ - Get alerts and notifications
