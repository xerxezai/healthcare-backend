from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'homeopathy'

router = DefaultRouter()
router.register(r'patients', views.HomeopathyPatientViewSet)
router.register(r'remedies', views.HomeopathyRemedyViewSet)
router.register(r'diagnoses', views.HomeopathyDiagnosisViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/ai-analysis/', views.AIAnalysisView.as_view(), name='ai-analysis'),
    path('api/remedy-search/', views.RemedySearchView.as_view(), name='remedy-search'),
    path('api/dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]
