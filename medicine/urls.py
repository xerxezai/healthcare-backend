from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet, DoctorViewSet, VitalSignsViewSet, AppointmentViewSet,
    PrescriptionViewSet, LabTestViewSet, EmergencyCaseViewSet,
    TreatmentPlanViewSet, MedicalRecordViewSet, DashboardViewSet,
    PatientReportViewSet, SOAPNoteViewSet, ProtocolSummarizerViewSet,
    ContractRedliningViewSet, PhysicianAssistantViewSet, AIBookingAssistantViewSet,
    InsurancePolicyCopilotViewSet, HospitalCSRAssistantViewSet, MedicalResearchReviewViewSet,
    BackOfficeAutomationViewSet, ClinicalHistorySearchViewSet, AdvancedFeaturesStatsView,
    # Diabetes views
    DiabetesPatientViewSet, BloodGlucoseReadingViewSet, HbA1cRecordViewSet,
    DiabetesMedicationViewSet, DiabetesComplicationScreeningViewSet,
    DiabetesEducationSessionViewSet, DiabetesEmergencyEventViewSet,
    DiabetesGoalViewSet, DiabetesDashboardViewSet,
    # Retinopathy AI views
    RetinopathyAIViewSet
)

# Import new S3-integrated API views
from .api_views import (
    # S3 Data Management Functions
    create_institution, create_patient, upload_medical_record,
    create_consultation, create_treatment_plan, store_lab_results,
    get_patient_medical_summary, get_medicine_analytics,
    # S3 ViewSets
    MedicalInstitutionViewSet, MedicinePatientViewSet, 
    MedicalRecordViewSet as S3MedicalRecordViewSet,
    ConsultationViewSet, TreatmentPlanViewSet as S3TreatmentPlanViewSet,
    LabResultViewSet, DoctorWorkspaceViewSet
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'vital-signs', VitalSignsViewSet, basename='vital-signs')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'lab-tests', LabTestViewSet, basename='lab-test')
router.register(r'emergency-cases', EmergencyCaseViewSet, basename='emergency-case')
router.register(r'treatment-plans', TreatmentPlanViewSet, basename='treatment-plan')
router.register(r'medical-records', MedicalRecordViewSet, basename='medical-record')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# New Feature Endpoints
router.register(r'patient-reports', PatientReportViewSet, basename='patient-report')
router.register(r'soap-notes', SOAPNoteViewSet, basename='soap-note')
router.register(r'protocol-summarizer', ProtocolSummarizerViewSet, basename='protocol-summarizer')
router.register(r'contract-redlining', ContractRedliningViewSet, basename='contract-redlining')
router.register(r'physician-assistant', PhysicianAssistantViewSet, basename='physician-assistant')
router.register(r'ai-booking-assistant', AIBookingAssistantViewSet, basename='ai-booking-assistant')
router.register(r'insurance-policy-copilot', InsurancePolicyCopilotViewSet, basename='insurance-policy-copilot')
router.register(r'hospital-csr-assistant', HospitalCSRAssistantViewSet, basename='hospital-csr-assistant')
router.register(r'medical-research-review', MedicalResearchReviewViewSet, basename='medical-research-review')
router.register(r'back-office-automation', BackOfficeAutomationViewSet, basename='back-office-automation')
router.register(r'clinical-history-search', ClinicalHistorySearchViewSet, basename='clinical-history-search')

# Advanced Features Combined Stats
router.register(r'advanced-features-stats', AdvancedFeaturesStatsView, basename='advanced-features-stats')

# Diabetes Management Endpoints
router.register(r'diabetes-patients', DiabetesPatientViewSet, basename='diabetes-patient')
router.register(r'glucose-readings', BloodGlucoseReadingViewSet, basename='glucose-reading')
router.register(r'hba1c-records', HbA1cRecordViewSet, basename='hba1c-record')
router.register(r'diabetes-medications', DiabetesMedicationViewSet, basename='diabetes-medication')
router.register(r'diabetes-screenings', DiabetesComplicationScreeningViewSet, basename='diabetes-screening')
router.register(r'diabetes-education', DiabetesEducationSessionViewSet, basename='diabetes-education')
router.register(r'diabetes-emergencies', DiabetesEmergencyEventViewSet, basename='diabetes-emergency')
router.register(r'diabetes-goals', DiabetesGoalViewSet, basename='diabetes-goal')
router.register(r'diabetes-dashboard', DiabetesDashboardViewSet, basename='diabetes-dashboard')

# Diabetic Retinopathy AI Endpoints
router.register(r'retinopathy-screenings', RetinopathyAIViewSet, basename='retinopathy-screening')

# S3-Integrated Medicine Data Management Endpoints
router.register(r's3-institutions', MedicalInstitutionViewSet, basename='s3-institution')
router.register(r's3-patients', MedicinePatientViewSet, basename='s3-patient')
router.register(r's3-medical-records', S3MedicalRecordViewSet, basename='s3-medical-record')
router.register(r's3-consultations', ConsultationViewSet, basename='s3-consultation')
router.register(r's3-treatment-plans', S3TreatmentPlanViewSet, basename='s3-treatment-plan')
router.register(r's3-lab-results', LabResultViewSet, basename='s3-lab-result')
router.register(r's3-doctor-workspaces', DoctorWorkspaceViewSet, basename='s3-doctor-workspace')

app_name = 'medicine'

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoints for retinopathy AI
    path('retinopathy-ai-analysis/', RetinopathyAIViewSet.as_view({'get': 'ai_analysis_results'}), name='retinopathy-ai-analysis'),
    path('fundus-images/', RetinopathyAIViewSet.as_view({'get': 'fundus_images'}), name='fundus-images'),
    path('analyze-retinopathy/', RetinopathyAIViewSet.as_view({'post': 'analyze_retinopathy'}), name='analyze-retinopathy'),
    path('generate-retinopathy-report/<int:pk>/', RetinopathyAIViewSet.as_view({'post': 'generate_report'}), name='generate-retinopathy-report'),
    
    # S3-Integrated Medicine Data Management API Endpoints
    path('s3-api/create-institution/', create_institution, name='s3-create-institution'),
    path('s3-api/create-patient/', create_patient, name='s3-create-patient'),
    path('s3-api/upload-medical-record/', upload_medical_record, name='s3-upload-medical-record'),
    path('s3-api/create-consultation/', create_consultation, name='s3-create-consultation'),
    path('s3-api/create-treatment-plan/', create_treatment_plan, name='s3-create-treatment-plan'),
    path('s3-api/store-lab-results/', store_lab_results, name='s3-store-lab-results'),
    path('s3-api/patient-summary/<uuid:patient_id>/', get_patient_medical_summary, name='s3-patient-summary'),
    path('s3-api/analytics/<uuid:institution_id>/', get_medicine_analytics, name='s3-medicine-analytics'),
]
