from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_s3.s3_views import (
    CosmetologySalonViewSet, CosmetologyClientS3ViewSet, 
    CosmetologyFileViewSet, CosmetologyAnalysisViewSet,
    cosmetology_analytics_view, cosmetology_sync_view, cosmetology_cleanup_view
)

app_name = 'cosmetology'

router = DefaultRouter()
# Original Cosmetology Routes
router.register(r'clients', views.CosmetologyClientViewSet)
router.register(r'services', views.CosmetologyServiceViewSet)
router.register(r'products', views.CosmetologyProductViewSet)
router.register(r'appointments', views.CosmetologyAppointmentViewSet)
router.register(r'treatment-plans', views.CosmetologyTreatmentPlanViewSet)
router.register(r'consultations', views.CosmetologyConsultationViewSet)
router.register(r'progress', views.CosmetologyProgressViewSet)

# S3 Data Management Routes
router.register(r's3-institutions', CosmetologySalonViewSet, basename='s3-institutions')
router.register(r's3-clients', CosmetologyClientS3ViewSet, basename='s3-clients')
router.register(r's3-files', CosmetologyFileViewSet, basename='s3-files')
router.register(r's3-analyses', CosmetologyAnalysisViewSet, basename='s3-analyses')

# Cosmetic Gynecology Routes - AI-Powered Medical Specialization
router.register(r'gynecology/clients', views.CosmeticGynecologyClientViewSet, basename='gynecology-clients')
router.register(r'gynecology/treatments', views.CosmeticGynecologyTreatmentViewSet, basename='gynecology-treatments')
router.register(r'gynecology/consultations', views.CosmeticGynecologyConsultationViewSet, basename='gynecology-consultations')
router.register(r'gynecology/treatment-plans', views.CosmeticGynecologyTreatmentPlanViewSet, basename='gynecology-treatment-plans')
router.register(r'gynecology/progress', views.CosmeticGynecologyProgressViewSet, basename='gynecology-progress')

urlpatterns = [
    path('', include(router.urls)),
    # Original Cosmetology API endpoints
    path('dashboard-stats/', views.CosmetologyDashboardStatsView.as_view(), name='dashboard-stats'),
    path('calendar/', views.AppointmentCalendarView.as_view(), name='appointment-calendar'),
    path('client-search/', views.ClientSearchView.as_view(), name='client-search'),
    path('service-recommendations/', views.ServiceRecommendationView.as_view(), name='service-recommendations'),
    
    # S3 Data Management API endpoints
    path('s3-analytics/', cosmetology_analytics_view, name='s3-analytics'),
    path('s3-sync/', cosmetology_sync_view, name='s3-sync'),
    path('cleanup-files/', cosmetology_cleanup_view, name='cleanup-files'),
    path('product-search/', views.ProductSearchView.as_view(), name='product-search'),
]
