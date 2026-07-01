import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "django-insecure-placeholder-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Allowed hosts
ALLOWED_HOSTS = ["*"]  # For development, refine for production
extra_hosts = os.getenv("ALLOWED_HOSTS", "")
if extra_hosts:
    ALLOWED_HOSTS.extend(filter(None, extra_hosts.split(",")))

# Railway production settings
RAILWAY_ENVIRONMENT_NAME = os.getenv("RAILWAY_ENVIRONMENT_NAME")
if RAILWAY_ENVIRONMENT_NAME == "production":
    ALLOWED_HOSTS.extend([
        ".railway.app",
        ".up.railway.app", 
        os.getenv("RAILWAY_PUBLIC_DOMAIN", ""),
    ])

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_ses",
    # Local apps
    "hospital",
    "secureneat",
    "radiology",
    "subscriptions",
    "dentistry",
    "dermatology",
    "cosmetology",
    # "allopathy",  # Temporarily disabled due to model conflicts
    "usage_tracking",
    "pathology",
    "medicine",
    "homeopathy",
    "netflix",
    "patients",
    "billing",  # Monthly subscription and manual billing management
    "dna_sequencing",  # AI-powered DNA sequencing and genomics
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Usually placed higher
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "subscriptions.middleware.SubscriptionMiddleware",  # Add subscription middleware after auth
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database (Railway PostgreSQL - Exclusive)
import dj_database_url

# Railway PostgreSQL Configuration (Exclusive - No Fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:TCxaXngnBHmwihKBGYAlYxCPFeIqbGOi@tramway.proxy.rlwy.net:17931/railway")

DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL)
}
# Note: The Node.js server.js had a MySQL connection pool.
# This Django setup assumes all data (including MCQs) will be in PostgreSQL.
# If you need to connect to an existing MySQL database for MCQs,
# you would configure a second database in DATABASES and use Django's
# multi-db features (e.g., database routers or .using('mysql_db') in queries).
# For simplicity and "clean modular code", migrating MCQ data to PostgreSQL is recommended.


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # For production collectstatic

# Media files (for user uploads if stored locally, not S3)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True  # For development only
else:
    # Production CORS settings
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if cors_origins:
        # Strip trailing slashes and whitespace from each origin
        CORS_ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in cors_origins.split(',')]
    else:
        # Fallback if no environment variable set
        CORS_ALLOWED_ORIGINS = [
            "https://frontend-6c2pzmsub-xerxezs-projects.vercel.app",
            "https://frontend-gamma-three-41.vercel.app",
            "https://xerxez.in",
            "https://www.xerxez.in",
        ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Session and CSRF settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'  # 'None' for cross-origin in production
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = not DEBUG  # True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'  # 'None' for cross-origin in production
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:5173",
    "https://www.xerxez.com",
    "https://xerxez.com",
    "https://mastermind-production-4a1a.up.railway.app",
]

# Custom user model
AUTH_USER_MODEL = "hospital.CustomUser"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'hospital.auth_backends.SimpleAuthBackend',
]

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",  # Default to requiring authentication
    ),
}

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google reCAPTCHA Settings
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

# Razorpay Settings
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# Frontend URL for payment redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Email Settings for Password Recovery
EMAIL_BACKEND = 'django_ses.SESBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Healthcare Platform <info@xerxez.in>')

# AWS SES Configuration (Primary Email Service)
AWS_SES_REGION = os.getenv('AWS_SES_REGION', 'us-east-1')
AWS_SNS_REGION = os.getenv('AWS_SNS_REGION', 'us-east-1')

# AWS Notification Service Settings
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SES_FROM_EMAIL = os.getenv('AWS_SES_FROM_EMAIL', 'info@xerxez.in')
AWS_SNS_SENDER_ID = os.getenv('AWS_SNS_SENDER_ID', 'Healthcare')

# Optional AWS Settings
AWS_SES_CONFIGURATION_SET = os.getenv('AWS_SES_CONFIGURATION_SET')
AWS_SNS_TOPIC_ARN = os.getenv('AWS_SNS_TOPIC_ARN')

# Support and Platform Settings
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@healthcare.com')
PLATFORM_NAME = os.getenv('PLATFORM_NAME', 'Healthcare Management Platform')

# Password Recovery Security Settings
PASSWORD_RESET_TIMEOUT = 900  # 15 minutes
PASSWORD_RESET_RATE_LIMIT = 3  # 3 attempts per IP/email per 5 minutes

# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_REGION", "ap-south-1")  # Default if not set
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_DEFAULT_ACL = None  # Or 'public-read' if you want files to be public by default
AWS_S3_FILE_OVERWRITE = (
    False  # Set to True if you want to overwrite files with the same name
)

# For serving static files from S3 (optional, if you want to go that route)
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage' # For media files

# Logging (Basic example, expand as needed)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# Password Policy Configuration (Soft-coded for easy customization)
try:
    from hospital.password_config import PASSWORD_POLICY, EMAIL_TEMPLATES, PASSWORD_LOGGING, FRONTEND_CONFIG
    
    # Import password policy settings
    PASSWORD_POLICY = PASSWORD_POLICY
    EMAIL_TEMPLATES = EMAIL_TEMPLATES
    PASSWORD_LOGGING = PASSWORD_LOGGING
    FRONTEND_CONFIG = FRONTEND_CONFIG
    
except ImportError:
    # Fallback configuration if password_config.py is not available
    PASSWORD_POLICY = {
        'min_length': 12,
        'max_length': 32,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special_chars': True,
        'auto_generate_for_admin': True,
        'force_password_change': True
    }

# Platform branding (can be customized for different deployments)
PLATFORM_NAME = os.getenv("PLATFORM_NAME", "Healthcare Management Platform")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "info@xerxez.in")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
