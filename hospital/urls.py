from django.urls import path, include
from .views import RegisterView, LoginView
from .comprehensive_registration_views import ComprehensiveRegistrationView
from rest_framework_simplejwt.views import TokenRefreshView

# Import notification views
from .notification_views import (
    send_test_notification,
    send_admin_notification,
    get_notification_logs,
    update_notification_preferences,
    get_notification_preferences,
    schedule_notification,
    get_scheduled_notifications,
    notification_system_status,
    # Enhanced notification views
    send_enhanced_notification,
    send_appointment_reminder,
    send_test_results_notification,
    send_emergency_alert,
    send_bulk_notifications,
    process_notification_queue
)

# Import AWS status view
from .aws_status_view import aws_service_status

# Import first login and password management views
from .first_login_views import (
    check_first_login_status,
    complete_first_login_setup,
    change_password,
    validate_password_strength
)

# Import contact form views
from .contact_views import submit_contact_form

# Import document upload views
from .registration_document_views import (
    RegistrationDocumentUploadView,
    RegistrationDocumentTypesView,
    RegistrationDocumentValidationView
)

# Import test views
from .test_views import test_endpoint

app_name = 'hospital_auth'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('comprehensive-register/', ComprehensiveRegistrationView.as_view(), name='comprehensive_register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Management System
    path('management/', include('hospital.user_management_urls')),
    
    # Document Upload System
    path('upload-registration-document/', RegistrationDocumentUploadView.as_view(), name='upload_registration_document'),
    path('registration-document-types/', RegistrationDocumentTypesView.as_view(), name='registration_document_types'),
    path('validate-registration-document/', RegistrationDocumentValidationView.as_view(), name='validate_registration_document'),
    
    # Notification System URLs
    path('notifications/test/', send_test_notification, name='send_test_notification'),
    path('notifications/admin/send/', send_admin_notification, name='send_admin_notification'),
    path('notifications/logs/', get_notification_logs, name='get_notification_logs'),
    path('notifications/preferences/', get_notification_preferences, name='get_notification_preferences'),
    path('notifications/preferences/update/', update_notification_preferences, name='update_notification_preferences'),
    path('notifications/schedule/', schedule_notification, name='schedule_notification'),
    path('notifications/scheduled/', get_scheduled_notifications, name='get_scheduled_notifications'),
    path('notifications/status/', notification_system_status, name='notification_system_status'),
    
    # Enhanced notification endpoints
    path('notifications/enhanced/send/', send_enhanced_notification, name='send_enhanced_notification'),
    path('notifications/appointment-reminder/', send_appointment_reminder, name='send_appointment_reminder'),
    path('notifications/test-results/', send_test_results_notification, name='send_test_results_notification'),
    path('notifications/emergency-alert/', send_emergency_alert, name='send_emergency_alert'),
    path('notifications/bulk/', send_bulk_notifications, name='send_bulk_notifications'),
    path('notifications/process-queue/', process_notification_queue, name='process_notification_queue'),
    path('notifications/aws-status/', aws_service_status, name='aws_service_status'),
    
    # First Login and Password Management
    path('auth/check-first-login/', check_first_login_status, name='check_first_login_status'),
    path('auth/complete-first-login/', complete_first_login_setup, name='complete_first_login_setup'),
    path('auth/change-password/', change_password, name='change_password'),
    path('auth/validate-password/', validate_password_strength, name='validate_password_strength'),
    
    # Contact Form
    path('contact/submit/', submit_contact_form, name='submit_contact_form'),
    
    # Test endpoint
    path('test/', test_endpoint, name='test_endpoint'),
]