# backend/notifications/urls.py

from django.urls import path, include
from . import views

app_name = 'notifications'

urlpatterns = [
    # Template management
    path('templates/', views.notification_templates, name='templates'),
    path('templates/<uuid:template_id>/', views.notification_template_detail, name='template_detail'),
    
    # User preferences
    path('preferences/', views.user_notification_preferences, name='user_preferences'),
    
    # Sending notifications
    path('send/', views.send_notification, name='send_notification'),
    
    # Notification history
    path('history/', views.notification_history, name='notification_history'),
    
    # Admin endpoints
    path('admin/stats/', views.admin_notification_stats, name='admin_stats'),
    path('admin/process-queue/', views.process_notification_queue, name='process_queue'),
    path('admin/email-providers/', views.email_providers, name='email_providers'),
    path('admin/sms-providers/', views.sms_providers, name='sms_providers'),
    
    # Healthcare-specific endpoints
    path('appointment-reminder/', views.send_appointment_reminder_api, name='appointment_reminder'),
    path('test-results/', views.send_test_results_api, name='test_results'),
    
    # Web interface
    path('dashboard/', views.notification_dashboard, name='dashboard'),
]
