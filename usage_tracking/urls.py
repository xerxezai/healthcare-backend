"""
Usage Tracking URL Configuration
"""

from django.urls import path, include
from . import views

app_name = 'usage_tracking'

urlpatterns = [
    # Core tracking endpoints
    path('track/', views.track_usage_event, name='track_usage'),
    path('summary/', views.get_usage_summary, name='usage_summary'),
    path('analytics/', views.get_usage_analytics, name='usage_analytics'),
    path('counters/', views.get_current_month_counters, name='current_month_counters'),
    
    # Dashboard integration
    path('dashboard/', views.dashboard_widget_data, name='dashboard_widgets'),
    
    # Alerts management
    path('alerts/', views.get_usage_alerts, name='usage_alerts'),
    path('alerts/<int:alert_id>/dismiss/', views.dismiss_alert, name='dismiss_alert'),
    path('alerts/<int:alert_id>/read/', views.mark_alert_read, name='mark_alert_read'),
    
    # Configuration
    path('categories/', views.get_usage_categories, name='usage_categories'),
    path('profile/', views.user_usage_profile, name='usage_profile'),
    path('initialize/', views.initialize_usage_tracking, name='initialize_tracking'),
    
    # Quick tracking endpoints
    path('track/patient/', views.track_patient_action, name='track_patient'),
    path('track/ai/', views.track_ai_action, name='track_ai'),
]
