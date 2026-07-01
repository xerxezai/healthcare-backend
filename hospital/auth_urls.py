from django.urls import path
from . import auth_views
from . import password_reset_views
from .comprehensive_registration_views import ComprehensiveRegistrationView

app_name = 'auth'

urlpatterns = [
    path('csrf-token/', auth_views.csrf_token_api, name='csrf_token'),
    path('login/', auth_views.login_api, name='login'),
    path('logout/', auth_views.logout_api, name='logout'),
    path('register/', auth_views.register_api, name='register'),
    path('comprehensive-register/', ComprehensiveRegistrationView.as_view(), name='comprehensive_register'),
    path('profile/', auth_views.user_profile_api, name='profile'),
    
    # Advanced Password Recovery System
    path('password-reset/initiate/', password_reset_views.initiate_password_reset, name='password_reset_initiate'),
    path('password-reset/validate/', password_reset_views.validate_reset_token, name='password_reset_validate'),
    path('password-reset/complete/', password_reset_views.reset_password_complete, name='password_reset_complete'),
    path('password-reset/status/', password_reset_views.password_reset_status, name='password_reset_status'),
]
