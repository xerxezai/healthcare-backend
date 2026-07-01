# Temporary settings for Railway deployment to bypass CustomUser migration issues
# This file can be used as a temporary replacement for settings.py

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

# Environment Variables (Emergency defaults to prevent AttributeError)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "emergency-placeholder-key")

# AWS Configuration (comprehensive)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "emergency-placeholder")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "emergency-placeholder")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "healthcare-emergency-bucket")

# Additional AWS settings that services expect
AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "healthcare-emergency-bucket")
AWS_S3_REGION_NAME = os.getenv("AWS_REGION", "ap-south-1")
AWS_SES_REGION = os.getenv("AWS_SES_REGION", "ap-south-1")
AWS_SNS_REGION = os.getenv("AWS_SNS_REGION", "ap-south-1")
AWS_SES_FROM_EMAIL = os.getenv("AWS_SES_FROM_EMAIL", "noreply@healthcare-emergency.com")

# Email settings (using environment variables)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Healthcare Emergency <noreply@healthcare.com>")

# Razorpay settings (emergency placeholders)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "emergency-placeholder")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "emergency-placeholder")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_ses",
    
    # Healthcare apps - TEMPORARILY EXCLUDING hospital app
    # "hospital",  # <-- COMMENTED OUT TO AVOID CustomUser ISSUES
    "medicine",
    "dentistry", 
    "dermatology",
    "pathology",
    "radiology",
    "cosmetology",
    "homeopathy",
    "patients",
    "netflix",
    "subscriptions",
    "secureneat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls_emergency"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# DO NOT USE CUSTOM USER MODEL TEMPORARILY
# AUTH_USER_MODEL = "hospital.CustomUser"  # <-- COMMENTED OUT

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://healthcare-production-1cab.up.railway.app",
]

CORS_ALLOW_CREDENTIALS = True

# Emergency configurations (bypass hospital.password_config imports)
PASSWORD_POLICY = {
    'MIN_LENGTH': 8,
    'REQUIRE_UPPERCASE': True,
    'REQUIRE_LOWERCASE': True, 
    'REQUIRE_DIGIT': True,
    'REQUIRE_SPECIAL_CHAR': False,
    'PREVENT_COMMON_PASSWORDS': True,
    'PREVENT_USER_INFO_IN_PASSWORD': True,
}

EMAIL_TEMPLATES = {
    'password_reset': {
        'subject': 'Password Reset - Healthcare Platform',
        'template': 'Password reset request received.'
    }
}

# Emergency logging (simplified)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}