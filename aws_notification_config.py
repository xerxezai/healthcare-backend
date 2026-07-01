# AWS SNS and SES Configuration for Healthcare Notifications
# Add these settings to your Django settings.py file

# =============================================================================
# AWS CREDENTIALS AND REGION
# =============================================================================

# AWS Access Credentials (use IAM user with limited permissions)
AWS_ACCESS_KEY_ID = 'your_aws_access_key_id_here'
AWS_SECRET_ACCESS_KEY = 'your_aws_secret_access_key_here'

# AWS Region (choose the region closest to your users)
AWS_REGION = 'us-east-1'  # or 'us-west-2', 'eu-west-1', etc.

# =============================================================================
# AWS SES (Simple Email Service) CONFIGURATION
# =============================================================================

# From email address (must be verified in SES)
AWS_SES_FROM_EMAIL = 'noreply@yourhealthcare.com'

# Configuration set name (optional, for tracking)
AWS_SES_CONFIGURATION_SET = 'healthcare-notifications'

# SES sending rate limits (optional)
AWS_SES_MAX_SEND_RATE = 14  # emails per second (default SES limit)

# =============================================================================
# AWS SNS (Simple Notification Service) CONFIGURATION
# =============================================================================

# SMS Sender ID (appears as sender name on SMS)
AWS_SNS_SENDER_ID = 'Healthcare'  # up to 11 characters

# SNS topic ARN for broadcast messages (optional)
AWS_SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789:healthcare-alerts'

# =============================================================================
# ENVIRONMENT VARIABLES (RECOMMENDED FOR PRODUCTION)
# =============================================================================

"""
For production, use environment variables instead of hardcoding credentials:

1. Create a .env file in your project root:

AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_SES_FROM_EMAIL=noreply@yourhealthcare.com
AWS_SNS_SENDER_ID=Healthcare

2. In settings.py, use:

import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_SES_FROM_EMAIL = os.getenv('AWS_SES_FROM_EMAIL')
AWS_SNS_SENDER_ID = os.getenv('AWS_SNS_SENDER_ID', 'Healthcare')
"""

# =============================================================================
# IAM PERMISSIONS REQUIRED
# =============================================================================

"""
Create an IAM user with the following policy for minimal permissions:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:GetSendQuota",
                "ses:GetSendStatistics"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish",
                "sns:ListTopics"
            ],
            "Resource": "*"
        }
    ]
}
"""

# =============================================================================
# AWS SETUP STEPS
# =============================================================================

"""
1. AWS SES Setup:
   a. Go to AWS SES Console
   b. Verify your sending domain (yourhealthcare.com)
   c. Verify your from email address
   d. Request production access (remove sandbox mode)
   e. Set up bounce and complaint handling

2. AWS SNS Setup:
   a. Go to AWS SNS Console
   b. Create topics for different alert types (optional)
   c. Configure SMS preferences for your region
   d. Set spending limits to control costs

3. Django Configuration:
   a. Install boto3: pip install boto3
   b. Add AWS credentials to settings.py or environment variables
   c. Test the connection using the aws_service_status endpoint

4. Testing:
   a. Start with SES sandbox mode for testing
   b. Use verified email addresses for initial testing
   c. Test SMS with your own phone number first
   d. Monitor AWS CloudWatch for delivery metrics
"""

# =============================================================================
# COST OPTIMIZATION
# =============================================================================

"""
AWS SES Pricing (as of 2024):
- First 62,000 emails per month: Free
- Additional emails: $0.10 per 1,000 emails

AWS SNS SMS Pricing (US):
- $0.0075 per SMS message (varies by country)
- International rates vary significantly

Cost Control Tips:
1. Set up billing alerts in AWS
2. Use SES suppression lists to avoid bounces
3. Implement user preferences to reduce volume
4. Monitor delivery rates and optimize templates
5. Use SNS topics for bulk messaging efficiency
"""

# =============================================================================
# HIPAA COMPLIANCE CONSIDERATIONS
# =============================================================================

"""
For HIPAA compliance with AWS:

1. Sign AWS Business Associate Agreement (BAA)
2. Use encrypted connections (TLS) - automatically handled
3. Enable CloudTrail for audit logging
4. Use VPC endpoints for private communication
5. Implement proper access controls and monitoring
6. Regular security assessments and penetration testing

Note: Standard SMS is not HIPAA compliant. For sensitive health information:
- Use secure patient portals instead of SMS
- Send only appointment reminders and general alerts via SMS
- Include disclaimers about communication security
"""

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================

# Enhanced logging configuration for AWS services
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'aws': {
            'format': '{levelname} {asctime} [AWS] {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'aws_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'aws_notifications.log',
            'formatter': 'aws',
        },
    },
    'loggers': {
        'hospital.aws_notification_service': {
            'handlers': ['aws_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'boto3': {
            'handlers': ['aws_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'botocore': {
            'handlers': ['aws_file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# =============================================================================
# FALLBACK CONFIGURATION
# =============================================================================

# The system will automatically fall back to these if AWS services fail:

# Twilio for SMS fallback
TWILIO_ACCOUNT_SID = 'your_twilio_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_token'
TWILIO_FROM_NUMBER = '+1234567890'

# SendGrid for email fallback
SENDGRID_API_KEY = 'your_sendgrid_key'
SENDGRID_FROM_EMAIL = 'backup@yourhealthcare.com'

# Django SMTP as final fallback
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yourdomain.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'smtp_user'
EMAIL_HOST_PASSWORD = 'smtp_password'
DEFAULT_FROM_EMAIL = 'noreply@yourhealthcare.com'
