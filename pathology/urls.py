from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'departments', views.PathologyDepartmentViewSet)
router.register(r'tests', views.PathologyTestViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'orders', views.PathologyOrderViewSet)
router.register(r'specimens', views.SpecimenViewSet)
router.register(r'reports', views.PathologyReportViewSet)
router.register(r'slides', views.DigitalSlideViewSet)
router.register(r'quality-control', views.PathologyQualityControlViewSet)

# S3 Data Management ViewSets
router.register(r's3-laboratories', views.PathologyLaboratoryViewSet)
router.register(r's3-patients', views.PathologyPatientViewSet)
router.register(r's3-specimens', views.PathologySpecimenViewSet)
router.register(r's3-files', views.PathologyFileViewSet)
router.register(r's3-analyses', views.PathologyAnalysisViewSet)

app_name = 'pathology'

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Dashboard and Analytics endpoints
    path('dashboard/', views.pathology_dashboard, name='dashboard'),
    path('analytics/', views.pathology_analytics, name='analytics'),
    path('test-statistics/', views.test_statistics, name='test_statistics'),
    
    # S3 Data Management endpoints
    path('s3-analytics/', views.pathology_s3_analytics, name='s3_analytics'),
    path('s3-sync/', views.pathology_s3_sync, name='s3_sync'),
    path('cleanup-files/', views.pathology_cleanup_files, name='cleanup_files'),
    path('generate-report/', views.generate_pathology_report, name='generate_report'),
]
