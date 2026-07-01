from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnonymizeDocumentView, 
    AnalyzeReportView, 
    ReportHistoryListView, 
    RadiologyMultimodalQueryView,
    AdvancedReportCorrectionView,
    AdvancedConfigurationView,
    ProcessingHistoryView,
    AdvancedAnalyzeReportView
)
from .api_views import (
    InstitutionViewSet,
    RadiologyPatientViewSet,
    RadiologyStudyViewSet,
    RadiologyReportViewSet,
    AIAnalysisResultViewSet,
    DoctorWorkspaceViewSet,
    create_patient,
    create_study,
    upload_dicom,
    create_report,
    store_ai_analysis,
    search_patients,
    search_studies,
    get_patient_studies,
    get_study_reports,
    get_analytics_dashboard
)
from .report_ai_correction import correct_radiology_report, get_knowledge_sources
from .advanced_report_ai import advanced_correct_radiology_report, get_advanced_configuration, get_processing_history
from .advanced_rads_calculator import (
    AdvancedRADSCalculatorView,
    get_ai_models,
    get_clinical_guidelines,
    validate_imaging_data
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet, basename='institutions')
router.register(r'patients', RadiologyPatientViewSet, basename='patients')
router.register(r'studies', RadiologyStudyViewSet, basename='studies')
router.register(r'reports', RadiologyReportViewSet, basename='reports')
router.register(r'ai-analyses', AIAnalysisResultViewSet, basename='ai-analyses')
router.register(r'doctor-workspaces', DoctorWorkspaceViewSet, basename='doctor-workspaces')

app_name = 'radiology'

urlpatterns = [
    # Include router URLs for the ViewSets
    path('api/', include(router.urls)),
    
    # S3 Data Management API endpoints
    path('api/create-patient/', create_patient, name='create_patient'),
    path('api/create-study/', create_study, name='create_study'),
    path('api/upload-dicom/', upload_dicom, name='upload_dicom'),
    path('api/create-report/', create_report, name='create_report'),
    path('api/store-ai-analysis/', store_ai_analysis, name='store_ai_analysis'),
    path('api/search/patients/', search_patients, name='search_patients'),
    path('api/search/studies/', search_studies, name='search_studies'),
    path('api/patient/<uuid:patient_id>/studies/', get_patient_studies, name='get_patient_studies'),
    path('api/study/<uuid:study_id>/reports/', get_study_reports, name='get_study_reports'),
    path('api/analytics/dashboard/', get_analytics_dashboard, name='analytics_dashboard'),
    
    # Legacy endpoints (for backward compatibility)
    path('anonymize-document/', AnonymizeDocumentView.as_view(), name='anonymize_document'),
    path('analyze-report/', AnalyzeReportView.as_view(), name='analyze_report'),
    path('advanced-analyze-report/', AdvancedAnalyzeReportView.as_view(), name='advanced_analyze_report'),
    path('history/', ReportHistoryListView.as_view(), name='report_history'),
    path('multimodal-query/', RadiologyMultimodalQueryView.as_view(), name='radiology_multimodal_query'),
    path('correct-report/', correct_radiology_report, name='correct_report'),
    path('knowledge-sources/', get_knowledge_sources, name='knowledge_sources'),
    path('advanced-correct-report/', advanced_correct_radiology_report, name='advanced_correct_report'),
    path('advanced-configuration/', get_advanced_configuration, name='advanced_configuration'),
    path('processing-history/', get_processing_history, name='processing_history'),
    
    # Advanced RADS Calculator endpoints
    path('advanced-rads/calculate/', AdvancedRADSCalculatorView.as_view(), name='advanced_rads_calculate'),
    path('advanced-rads/models/', get_ai_models, name='get_ai_models'),
    path('advanced-rads/guidelines/', get_clinical_guidelines, name='get_clinical_guidelines'),
    path('advanced-rads/validate-images/', validate_imaging_data, name='validate_imaging_data'),
    
    # Voice Recognition & Reporting Tools
    path('voice/', include('radiology.voice_urls')),
]