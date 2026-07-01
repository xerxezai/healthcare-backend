# Enhanced Notification Service Configuration
# Add these settings to your Django settings.py file

# =============================================================================
# SMS CONFIGURATION (Twilio)
# =============================================================================
# Sign up at https://www.twilio.com/ to get these credentials

# Twilio Account SID
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid_here'

# Twilio Auth Token
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token_here'

# Twilio Phone Number (the number you'll send SMS from)
TWILIO_FROM_NUMBER = '+1234567890'

# =============================================================================
# EMAIL CONFIGURATION (SendGrid)
# =============================================================================
# Sign up at https://sendgrid.com/ to get API key

# SendGrid API Key
SENDGRID_API_KEY = 'your_sendgrid_api_key_here'

# SendGrid From Email (must be verified in SendGrid)
SENDGRID_FROM_EMAIL = 'noreply@yourdomain.com'

# =============================================================================
# DJANGO EMAIL FALLBACK CONFIGURATION
# =============================================================================
# Used when SendGrid is not available or configured

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Change to your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'

# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

# Quiet hours for non-critical SMS notifications (24-hour format)
NOTIFICATION_QUIET_HOURS_START = 21  # 9 PM
NOTIFICATION_QUIET_HOURS_END = 8     # 8 AM

# Maximum retry attempts for failed notifications
NOTIFICATION_MAX_RETRIES = 3

# Batch size for processing scheduled notifications
NOTIFICATION_BATCH_SIZE = 50

# Rate limiting (notifications per minute)
NOTIFICATION_RATE_LIMIT = 100

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'notifications.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'hospital.enhanced_notification_service': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'hospital.notification_views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# =============================================================================
# CELERY CONFIGURATION (Optional - for async processing)
# =============================================================================

# Redis as Celery broker (install redis-server)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery beat schedule for processing notifications
CELERY_BEAT_SCHEDULE = {
    'process-notifications': {
        'task': 'hospital.tasks.process_scheduled_notifications',
        'schedule': 60.0,  # Run every minute
    },
}

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

"""
For production, use environment variables instead of hardcoding credentials:

1. Create a .env file in your project root:

TWILIO_ACCOUNT_SID=your_actual_sid
TWILIO_AUTH_TOKEN=your_actual_token
TWILIO_FROM_NUMBER=+1234567890
SENDGRID_API_KEY=your_actual_api_key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

2. In settings.py, use:

import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL')
"""

# =============================================================================
# REQUIRED PACKAGES
# =============================================================================

"""
Add these to your requirements.txt:

twilio>=8.0.0
sendgrid>=6.0.0
celery>=5.0.0
redis>=4.0.0
python-dotenv>=0.19.0
"""
