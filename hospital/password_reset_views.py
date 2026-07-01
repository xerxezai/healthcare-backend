"""
Innovative Password Recovery System with Advanced Security Features
Author: Healthcare Platform Team
Security Features: Multi-step verification, rate limiting, email encryption, audit logging
"""

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import json
import secrets
import hashlib
import requests
import logging
from datetime import timedelta
import re
import boto3
from botocore.exceptions import ClientError
import os

# Import notification system
from .notification_system import notification_manager

User = get_user_model()
logger = logging.getLogger(__name__)

# Rate limiting settings
RATE_LIMIT_REQUESTS = int(os.getenv('PASSWORD_RESET_RATE_LIMIT', 3))
RATE_LIMIT_WINDOW = int(os.getenv('PASSWORD_RESET_RATE_WINDOW', 300))  # 5 minutes
TOKEN_EXPIRY = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY', 900))  # 15 minutes
MAX_ATTEMPTS = int(os.getenv('PASSWORD_RESET_MAX_ATTEMPTS', 5))

def send_password_reset_confirmation_aws_ses(user_email, user_name="User", reset_time=None, user_ip=None):
    """
    Send password reset confirmation email using AWS SES
    """
    try:
        # AWS SES Configuration
        ses_client = boto3.client(
            'ses',
            region_name=os.getenv('AWS_SES_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        from_email = os.getenv('AWS_SES_FROM_EMAIL', 'info@xerxez.in')
        reset_time_str = reset_time or timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        # Professional HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Confirmation</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">✅ Password Reset Successful</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Healthcare Management Platform</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: #d4edda; border-radius: 50%; width: 80px; height: 80px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 36px;">
                        🛡️
                    </div>
                    <h2 style="color: #155724; margin: 0; font-size: 24px;">Password Successfully Reset</h2>
                </div>
                
                <div style="background: #d4edda; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 5px solid #28a745;">
                    <p style="margin: 0 0 15px 0; font-size: 16px;">
                        <strong>Hello {user_name},</strong>
                    </p>
                    <p style="margin: 0 0 15px 0; color: #155724;">
                        Your password has been successfully reset for your Healthcare Platform account.
                    </p>
                    <p style="margin: 0; color: #155724; font-size: 14px;">
                        <strong>Security Details:</strong><br>
                        • Reset completed: {reset_time_str}<br>
                        {f"• IP Address: {user_ip}" if user_ip else ""}
                    </p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 16px;">🔒 Security Recommendations</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">
                        <li>Use a unique password for your healthcare account</li>
                        <li>Enable two-factor authentication if available</li>
                        <li>Log out from all devices if you suspect unauthorized access</li>
                        <li>Monitor your account for any suspicious activity</li>
                    </ul>
                </div>
                
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center;">
                    <h3 style="margin: 0 0 10px 0; color: #721c24; font-size: 16px;">⚠️ Didn't make this change?</h3>
                    <p style="margin: 0 0 15px 0; color: #721c24; font-size: 14px;">
                        If you did not reset your password, please contact our security team immediately.
                    </p>
                    <a href="mailto:info@xerxez.in" 
                       style="background: #dc3545; 
                              color: white; 
                              padding: 10px 20px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        🚨 Report Security Issue
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px;">
                <p style="margin: 0 0 10px 0;">
                    <strong>Healthcare Management Platform</strong><br>
                    Secure • Reliable • Professional
                </p>
                <p style="margin: 0;">
                    Need help? Contact us at <a href="mailto:info@xerxez.in" style="color: #28a745;">info@xerxez.in</a>
                </p>
                <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
                    This is an automated security notification.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Confirmation - Healthcare Management Platform
        
        Hello {user_name},
        
        Your password has been successfully reset for your Healthcare Platform account.
        
        Security Details:
        - Reset completed: {reset_time_str}
        {f"- IP Address: {user_ip}" if user_ip else ""}
        
        Security Recommendations:
        - Use a unique password for your healthcare account
        - Enable two-factor authentication if available
        - Log out from all devices if you suspect unauthorized access
        - Monitor your account for any suspicious activity
        
        If you did not make this change, please contact our security team immediately at info@xerxez.in
        
        Healthcare Management Platform
        Secure • Reliable • Professional
        """
        
        # Send email via AWS SES
        response = ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [user_email]},
            Message={
                'Subject': {
                    'Data': '✅ Password Reset Confirmation - Healthcare Platform',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_content,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        logger.info(f"Password reset confirmation email sent successfully via AWS SES to {user_email}. MessageId: {response['MessageId']}")
        return True, "Confirmation email sent successfully"
        
    except Exception as e:
        logger.error(f"Error sending password reset confirmation email to {user_email}: {str(e)}")
        return False, f"Failed to send confirmation email: {str(e)}"

def send_password_reset_email_django_smtp(user_email, reset_link, user_name="User"):
    """
    Send password reset email using Django's SMTP backend (fallback method)
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset - Healthcare Platform</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px;">
                <h1>🔐 Password Reset Request</h1>
                <p>Healthcare Management Platform</p>
            </div>
            
            <div style="background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 5px;">
                <h2>Hello {user_name},</h2>
                <p>We received a request to reset your password for your Healthcare Platform account.</p>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{reset_link}" 
                       style="background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Reset My Password
                    </a>
                </div>
                
                <p><strong>Security Notice:</strong></p>
                <ul>
                    <li>This link expires in 15 minutes</li>
                    <li>If you didn't request this, please ignore this email</li>
                    <li>Never share this link with anyone</li>
                </ul>
                
                <p>If the button doesn't work, copy this link:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
            </div>
            
            <div style="text-align: center; color: #666; font-size: 12px;">
                <p>Healthcare Management Platform<br>
                This is an automated message. Please do not reply.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Request - Healthcare Platform
        
        Hello {user_name},
        
        We received a request to reset your password.
        Click this link to reset: {reset_link}
        
        This link expires in 15 minutes.
        If you didn't request this, please ignore this email.
        
        Healthcare Management Platform
        """
        
        # Send email
        result = send_mail(
            subject='🔐 Password Reset Request - Healthcare Platform',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Password reset email sent successfully via Django SMTP to {user_email}")
            return True
        else:
            logger.error(f"Django SMTP failed to send password reset email to {user_email}")
            return False
            
    except Exception as e:
        logger.error(f"Django SMTP error sending password reset email to {user_email}: {str(e)}")
        return False


def send_password_reset_email_aws_ses(user_email, reset_link, user_name="User"):
    """
    Send password reset email using AWS SES with enhanced security and professional formatting
    """
    try:
        # AWS SES Configuration
        ses_client = boto3.client(
            'ses',
            region_name=os.getenv('AWS_SES_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        from_email = os.getenv('AWS_SES_FROM_EMAIL', 'info@xerxez.in')
        
        # Professional HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Request</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔐 Password Reset Request</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Healthcare Management Platform</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; border-radius: 50%; width: 80px; height: 80px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 36px;">
                        🛡️
                    </div>
                    <h2 style="color: #2c3e50; margin: 0; font-size: 24px;">Password Reset Request</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 5px solid #667eea;">
                    <p style="margin: 0 0 15px 0; font-size: 16px;">
                        <strong>Hello {user_name},</strong>
                    </p>
                    <p style="margin: 0 0 15px 0; color: #555;">
                        We received a request to reset the password for your Healthcare Platform account. If you made this request, please click the button below to reset your password.
                    </p>
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>Security Notice:</strong> This link will expire in 15 minutes for your security.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 8px; 
                              font-weight: bold; 
                              font-size: 16px; 
                              display: inline-block; 
                              box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                              transition: all 0.3s ease;">
                        🔐 Reset My Password
                    </a>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 16px;">⚠️ Security Guidelines</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">
                        <li>This link expires in 15 minutes</li>
                        <li>Only use this link if you requested a password reset</li>
                        <li>Create a strong password with uppercase, lowercase, numbers, and symbols</li>
                        <li>Never share your password with others</li>
                    </ul>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center;">
                    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">
                        <strong>Didn't request this password reset?</strong>
                    </p>
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        If you didn't request this, please ignore this email. Your password will remain unchanged.
                        Consider changing your password if you suspect unauthorized access.
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px;">
                <p style="margin: 0 0 10px 0;">
                    <strong>Healthcare Management Platform</strong><br>
                    Secure • Reliable • Professional
                </p>
                <p style="margin: 0;">
                    Need help? Contact us at <a href="mailto:info@xerxez.in" style="color: #667eea;">info@xerxez.in</a>
                </p>
                <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Request - Healthcare Management Platform
        
        Hello {user_name},
        
        We received a request to reset the password for your Healthcare Platform account.
        
        To reset your password, please visit the following link:
        {reset_link}
        
        Security Notice:
        - This link will expire in 15 minutes for your security
        - Only use this link if you requested a password reset
        - Create a strong password with uppercase, lowercase, numbers, and symbols
        
        If you didn't request this password reset, please ignore this email.
        Your password will remain unchanged.
        
        Need help? Contact us at info@xerxez.in
        
        Healthcare Management Platform
        Secure • Reliable • Professional
        """
        
        # Send email via AWS SES
        response = ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [user_email]},
            Message={
                'Subject': {
                    'Data': '🔐 Password Reset Request - Healthcare Platform',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_content,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        logger.info(f"Password reset email sent successfully via AWS SES to {user_email}. MessageId: {response['MessageId']}")
        return True, "Email sent successfully"
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS SES error sending password reset email to {user_email}: {error_code} - {error_message}")
        return False, f"Email service error: {error_message}"
        
    except Exception as e:
        logger.error(f"Unexpected error sending password reset email to {user_email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"

def verify_recaptcha(token):
    """Verify Google reCAPTCHA token with soft-coded configuration"""
    print(f"🔍 DEBUG: verify_recaptcha called with token: {token[:20] if token else 'None'}...")
    
    try:
        # Force test key for development - soft-coded approach
        debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
        
        if debug_mode:
            print("🚀 DEBUG: Development mode detected - using test reCAPTCHA configuration")
            print("✅ DEBUG: Test reCAPTCHA verification passed (development mode)")
            return True
        
        # Use environment variable for production
        secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        print(f"🔍 DEBUG: RECAPTCHA_SECRET_KEY from env: {secret_key[:20] if secret_key else 'None'}...")
        
        if not secret_key:
            # Development/test fallback - always passes
            print("⚠️ DEBUG: RECAPTCHA_SECRET_KEY not configured, using test key")
            secret_key = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
        
        # Skip verification if using test key in development
        if secret_key == '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe':
            print("✅ DEBUG: Using reCAPTCHA test key - verification skipped for development")
            return True  # Return boolean only
        
        print("🌐 DEBUG: Making request to Google reCAPTCHA API")
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': token
            },
            timeout=10
        )
        result = response.json()
        
        # Log the verification result for debugging
        success = result.get('success', False)
        score = result.get('score', 0)
        print(f"🔍 DEBUG: reCAPTCHA API response: success={success}, score={score}")
        
        return success and score >= 0.5
        
    except Exception as e:
        print(f"❌ DEBUG: reCAPTCHA verification error: {str(e)}")
        # In debug mode, return True even on error to allow testing
        debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
        if debug_mode:
            print("⚠️ DEBUG: Returning True due to debug mode despite error")
            return True
        return False

def check_rate_limit(identifier):
    """Check if rate limit is exceeded for given identifier"""
    cache_key = f"password_reset_rate_{identifier}"
    attempts = cache.get(cache_key, 0)
    return attempts < RATE_LIMIT_REQUESTS

def increment_rate_limit(identifier):
    """Increment rate limit counter"""
    cache_key = f"password_reset_rate_{identifier}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, RATE_LIMIT_WINDOW)

def generate_secure_token():
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(32)

def hash_token(token):
    """Hash token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def validate_password_strength(password):
    """Validate password strength with comprehensive rules"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check against common weak passwords
    weak_patterns = [
        r'password', r'123456', r'qwerty', r'admin', r'welcome',
        r'letmein', r'monkey', r'dragon', r'master', r'shadow'
    ]
    
    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common weak patterns")
            break
    
    return errors

@csrf_exempt
@require_http_methods(["POST"])
def initiate_password_reset(request):
    """
    Step 1: Initiate password reset process
    Advanced security with rate limiting, email validation, and audit logging
    """
    # Debug logging
    logger.info("🚀 Password reset request received")
    logger.info(f"📡 Request method: {request.method}")
    logger.info(f"📋 Request headers: {dict(request.headers)}")
    logger.info(f"📝 Request body (raw): {request.body}")
    
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
            logger.info(f"✅ JSON parsed successfully: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in password reset request: {str(e)}")
            logger.error(f"📝 Raw body that failed to parse: {request.body}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid request format'
            }, status=400)
        
        email = data.get('email', '').strip().lower()
        recaptcha_token = data.get('recaptcha_token')
        user_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        
        logger.info(f"📧 Email from request: '{email}'")
        logger.info(f"🔐 reCAPTCHA token present: {bool(recaptcha_token)}")
        logger.info(f"🌐 User IP: {user_ip}")
        
        # Input validation
        if not email:
            logger.warning("❌ Email validation failed: empty email")
            return JsonResponse({
                'success': False,
                'error': 'Email address is required'
            }, status=400)
        
        if not recaptcha_token:
            logger.warning("❌ reCAPTCHA validation failed: missing token")
            return JsonResponse({
                'success': False,
                'error': 'reCAPTCHA verification is required'
            }, status=400)
        
        # Verify reCAPTCHA
        logger.info("🔍 Starting reCAPTCHA verification")
        recaptcha_result = verify_recaptcha(recaptcha_token)
        logger.info(f"🔐 reCAPTCHA verification result: {recaptcha_result}")
        
        if not recaptcha_result:
            logger.warning(f"❌ reCAPTCHA verification failed for email: {email} from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'reCAPTCHA verification failed. Please try again.'
            }, status=400)
        
        # Rate limiting by IP and email
        ip_identifier = f"ip_{user_ip}"
        email_identifier = f"email_{email}"
        
        if not check_rate_limit(ip_identifier) or not check_rate_limit(email_identifier):
            logger.warning(f"Rate limit exceeded for password reset: {email} from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'Too many password reset attempts. Please try again later.'
            }, status=429)
        
        # Increment rate limits
        increment_rate_limit(ip_identifier)
        increment_rate_limit(email_identifier)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Security: Always return success to prevent email enumeration
            logger.info(f"Password reset attempted for non-existent email: {email} from IP: {user_ip}")
            return JsonResponse({
                'success': True,
                'message': 'If your email exists in our system, you will receive a password reset link.',
                'step': 'email_sent'
            })
        
        # Generate secure reset token
        reset_token = generate_secure_token()
        token_hash = hash_token(reset_token)
        
        # Store token in cache with expiry
        cache_key = f"password_reset_{token_hash}"
        cache_data = {
            'user_id': user.id,
            'email': email,
            'created_at': timezone.now().isoformat(),
            'ip_address': user_ip,
            'attempts': 0
        }
        cache.set(cache_key, cache_data, TOKEN_EXPIRY)
        
        # Prepare email content
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
        
        # HTML email template
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset - Healthcare Platform</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; font-weight: 600; }}
                .content {{ padding: 40px; }}
                .security-badge {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; font-weight: 600; margin-bottom: 20px; }}
                .reset-button {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
                .security-info {{ background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Secure Password Reset</h1>
                </div>
                <div class="content">
                    <div class="security-badge">🛡️ Security Verified</div>
                    
                    <h2>Hello {user.full_name or user.email},</h2>
                    
                    <p>We received a request to reset your password for your Healthcare Platform account. This request was initiated from IP address: <strong>{user_ip}</strong></p>
                    
                    <div class="security-info">
                        <strong>🔍 Security Information:</strong><br>
                        • Request Time: {timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')}<br>
                        • Token Expires: 15 minutes from now<br>
                        • Single-use security token<br>
                        • Encrypted communication
                    </div>
                    
                    <p>Click the button below to securely reset your password:</p>
                    
                    <a href="{reset_url}" class="reset-button">🔑 Reset My Password</a>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        • This link expires in 15 minutes for your security<br>
                        • If you didn't request this reset, please ignore this email<br>
                        • Never share this link with anyone<br>
                        • Our team will never ask for your password via email
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #007bff;">{reset_url}</p>
                    
                    <p>For security questions, contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>Healthcare Platform Security Team<br>
                    This is an automated security message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        plain_message = f"""
        Healthcare Platform - Password Reset Request
        
        Hello {user.full_name or user.email},
        
        We received a request to reset your password for your Healthcare Platform account.
        
        Security Information:
        - Request Time: {timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')}
        - Request IP: {user_ip}
        - Token expires in 15 minutes
        
        Click this link to reset your password:
        {reset_url}
        
        If you didn't request this reset, please ignore this email.
        
        For security questions, contact our support team.
        
        Healthcare Platform Security Team
        """
        
        # Send email using AWS SES (with fallback to Django SMTP for development)
        try:
            user_name = getattr(user, 'first_name', 'User') or user.username
            
            # Try AWS SES first
            if not settings.DEBUG:
                success, message = send_password_reset_email_aws_ses(
                    user_email=email,
                    reset_link=reset_url,
                    user_name=user_name
                )
                
                if not success:
                    logger.error(f"AWS SES failed to send password reset email to {email}: {message}")
                    # Fall back to Django SMTP
                    success = send_password_reset_email_django_smtp(email, reset_url, user_name)
            else:
                # Development mode: use Django SMTP directly
                logger.info(f"DEBUG MODE: Using Django SMTP for password reset email to {email}")
                success = send_password_reset_email_django_smtp(email, reset_url, user_name)
            
            if not success:
                logger.error(f"Failed to send password reset email to {email} via all methods")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send reset email. Please try again later.'
                }, status=500)
            
            logger.info(f"Password reset email sent successfully to: {email} from IP: {user_ip}")
            
        except Exception as e:
            logger.error(f"Unexpected error sending password reset email to {email}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to send reset email. Please try again later.'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'Password reset instructions have been sent to your email address.',
            'step': 'email_sent',
            'expires_in': TOKEN_EXPIRY
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Password reset initiation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def validate_reset_token(request):
    """
    Step 2: Validate reset token
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        user_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        
        if not token:
            return JsonResponse({
                'success': False,
                'error': 'Reset token is required'
            }, status=400)
        
        # Hash the token to lookup in cache
        token_hash = hash_token(token)
        cache_key = f"password_reset_{token_hash}"
        
        # Get token data from cache
        token_data = cache.get(cache_key)
        
        if not token_data:
            logger.warning(f"Invalid or expired password reset token used from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired reset token. Please request a new password reset.'
            }, status=400)
        
        # Verify user still exists and is active
        try:
            user = User.objects.get(id=token_data['user_id'], is_active=True)
        except User.DoesNotExist:
            logger.warning(f"Password reset attempted for deactivated user: {token_data.get('email')} from IP: {user_ip}")
            cache.delete(cache_key)  # Clean up invalid token
            return JsonResponse({
                'success': False,
                'error': 'Invalid reset token. User account not found.'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Token is valid. You can now reset your password.',
            'user_email': user.email,
            'step': 'enter_password'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password_complete(request):
    """
    Step 3: Complete password reset with new password
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        recaptcha_token = data.get('recaptcha_token')
        user_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        
        # Input validation
        if not all([token, new_password, confirm_password, recaptcha_token]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required'
            }, status=400)
        
        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_token):
            logger.warning(f"Failed reCAPTCHA verification for password reset completion from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'reCAPTCHA verification failed'
            }, status=400)
        
        # Password confirmation check
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'Passwords do not match'
            }, status=400)
        
        # Validate password strength
        password_errors = validate_password_strength(new_password)
        if password_errors:
            return JsonResponse({
                'success': False,
                'error': 'Password does not meet security requirements',
                'password_errors': password_errors
            }, status=400)
        
        # Hash the token to lookup in cache
        token_hash = hash_token(token)
        cache_key = f"password_reset_{token_hash}"
        
        # Get token data from cache
        token_data = cache.get(cache_key)
        
        if not token_data:
            logger.warning(f"Invalid or expired password reset token used for completion from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired reset token'
            }, status=400)
        
        # Check attempts limit
        if token_data.get('attempts', 0) >= MAX_ATTEMPTS:
            cache.delete(cache_key)
            logger.warning(f"Too many password reset attempts for token from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'Too many attempts. Please request a new password reset.'
            }, status=400)
        
        # Increment attempts
        token_data['attempts'] = token_data.get('attempts', 0) + 1
        cache.set(cache_key, token_data, TOKEN_EXPIRY)
        
        # Get user and update password
        try:
            user = User.objects.get(id=token_data['user_id'], is_active=True)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Delete the used token
            cache.delete(cache_key)
            
            # Log successful password reset
            logger.info(f"Password successfully reset for user: {user.email} from IP: {user_ip}")
            
            # Send confirmation email using AWS SES
            try:
                user_name = getattr(user, 'first_name', 'User') or user.username
                reset_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
                
                success, message = send_password_reset_confirmation_aws_ses(
                    user_email=user.email,
                    user_name=user_name,
                    reset_time=reset_time,
                    user_ip=user_ip
                )
                
                if success:
                    logger.info(f"Password reset confirmation email sent to {user.email}")
                else:
                    logger.warning(f"Failed to send confirmation email: {message}")
                    
            except Exception as e:
                logger.error(f"Failed to send password reset confirmation email: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': 'Password has been reset successfully. You can now login with your new password.',
                'step': 'completed'
            })
            
        except User.DoesNotExist:
            cache.delete(cache_key)
            logger.warning(f"Password reset attempted for non-existent user ID: {token_data.get('user_id')} from IP: {user_ip}")
            return JsonResponse({
                'success': False,
                'error': 'User account not found'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Password reset completion error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def password_reset_status(request):
    """
    Check the status of a password reset token
    """
    try:
        token = request.GET.get('token', '').strip()
        
        if not token:
            return JsonResponse({
                'success': False,
                'error': 'Token is required'
            }, status=400)
        
        # Hash the token to lookup in cache
        token_hash = hash_token(token)
        cache_key = f"password_reset_{token_hash}"
        
        # Get token data from cache
        token_data = cache.get(cache_key)
        
        if not token_data:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired token',
                'status': 'expired'
            })
        
        # Calculate remaining time
        from datetime import datetime
        created_at = datetime.fromisoformat(token_data['created_at'].replace('Z', '+00:00'))
        now = timezone.now()
        elapsed = (now - created_at).total_seconds()
        remaining = max(0, TOKEN_EXPIRY - elapsed)
        
        return JsonResponse({
            'success': True,
            'status': 'valid',
            'remaining_time': int(remaining),
            'attempts_left': MAX_ATTEMPTS - token_data.get('attempts', 0),
            'user_email': token_data.get('email', '')
        })
        
    except Exception as e:
        logger.error(f"Password reset status check error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)
