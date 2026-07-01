from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientListCreateView, PatientDetailView, PatientSummaryListView,
    MedicalHistoryListCreateView, MedicalHistoryDetailView,
    AppointmentListCreateView, AppointmentDetailView, TodayAppointmentsView,
    VitalSignsListCreateView, VitalSignsDetailView,
    LabResultListCreateView, LabResultDetailView,
    patient_dashboard_stats, doctors_list, patient_search,
    bulk_appointment_update, appointment_calendar_data
)
from .advanced_views import (
    PatientAdmissionViewSet, PatientJourneyViewSet, PatientReportViewSet,
    AIPatientInsightsViewSet, PatientAnalyticsViewSet
)

# Create router for advanced patient management APIs
router = DefaultRouter()
router.register(r'admissions', PatientAdmissionViewSet, basename='admission')
router.register(r'journey', PatientJourneyViewSet, basename='journey')
router.register(r'reports', PatientReportViewSet, basename='report')
router.register(r'ai-insights', AIPatientInsightsViewSet, basename='ai-insights')
router.register(r'analytics', PatientAnalyticsViewSet, basename='analytics')

app_name = 'patients'

urlpatterns = [
    # Patient endpoints
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('patients/summary/', PatientSummaryListView.as_view(), name='patient-summary'),
    path('patients/search/', patient_search, name='patient-search'),
    
    # Medical History endpoints
    path('medical-history/', MedicalHistoryListCreateView.as_view(), name='medical-history-list-create'),
    path('medical-history/<int:pk>/', MedicalHistoryDetailView.as_view(), name='medical-history-detail'),
    
    # Appointment endpoints
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/today/', TodayAppointmentsView.as_view(), name='today-appointments'),
    path('appointments/calendar/', appointment_calendar_data, name='appointment-calendar'),
    path('appointments/bulk-update/', bulk_appointment_update, name='bulk-appointment-update'),
    
    # Vital Signs endpoints
    path('vital-signs/', VitalSignsListCreateView.as_view(), name='vital-signs-list-create'),
    path('vital-signs/<int:pk>/', VitalSignsDetailView.as_view(), name='vital-signs-detail'),
    
    # Lab Results endpoints
    path('lab-results/', LabResultListCreateView.as_view(), name='lab-results-list-create'),
    path('lab-results/<int:pk>/', LabResultDetailView.as_view(), name='lab-results-detail'),
    
    # Dashboard and utilities
    path('dashboard/stats/', patient_dashboard_stats, name='patient-dashboard-stats'),
    path('doctors/', doctors_list, name='doctors-list'),
    
    # Advanced Patient Management APIs
    path('api/v2/', include(router.urls)),
]
