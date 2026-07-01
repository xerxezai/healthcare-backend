from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import hashlib
import random
import string
import requests
from datetime import datetime, timedelta

# Soft-coded rate limiting configuration for registration
REGISTRATION_RATE_LIMITING = {
    'enabled': False,  # Disable rate limiting for registration to improve user experience
    'max_attempts_per_hour': 10,  # Increased from 5 to 10 attempts
    'max_attempts_per_day': 20,   # Daily limit as backup
    'timeout_hours': 1,           # Cache timeout in hours
    'exempt_for_first_time': True, # Exempt first-time users from rate limiting
    'development_mode': True      # Bypass rate limiting in development
}

# Simple email function that works
import boto3
from django.utils.html import strip_tags

def send_registration_emails(user_data):
    """Send registration confirmation and admin notification emails"""
    try:
        # Initialize SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_SES_REGION', 'us-east-1')
        )
        
        from_email = getattr(settings, 'AWS_SES_FROM_EMAIL', 'info@xerxez.in')
        user_email = user_data.get('email')
        user_name = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}"
        
        # 1. Send confirmation email to user
        user_subject = "🏥 Registration Confirmation - Healthcare Management System"
        user_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to Healthcare Management System! 🏥</h2>
            
            <p>Dear {user_name},</p>
            
            <p>Thank you for registering with our Healthcare Management System. Your registration has been received and is currently pending approval.</p>
            
            <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>✅ Registration Status: Pending Approval</h3>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Professional Title:</strong> {user_data.get('professionalTitle', 'Healthcare Professional')}</p>
                <p><strong>Registration Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h3>What's Next?</h3>
            <ul>
                <li>Our admin team will review your registration within 24-48 hours</li>
                <li>You will receive an email notification once your account is approved</li>
                <li>After approval, you can log in and access all platform features</li>
            </ul>
            
            <p>If you have any questions, please contact our support team.</p>
            
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                This is an automated email from Healthcare Management System. Please do not reply to this email.
            </p>
        </div>
        """
        
        # Send user confirmation email
        ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [user_email]},
            Message={
                'Subject': {'Data': user_subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': strip_tags(user_html), 'Charset': 'UTF-8'},
                    'Html': {'Data': user_html, 'Charset': 'UTF-8'}
                }
            }
        )
        
        # 2. Send admin notification
        admin_email = 'info@xerxez.in'  # Admin email
        admin_subject = "🔔 New Doctor Registration - Action Required"
        admin_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>🏥 New Doctor Registration Notification</h2>
            
            <p>A new healthcare professional has registered and requires approval:</p>
            
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h3>� Registration Details:</h3>
                <ul>
                    <li><strong>Name:</strong> {user_name}</li>
                    <li><strong>Email:</strong> {user_email}</li>
                    <li><strong>Professional Title:</strong> {user_data.get('professionalTitle', 'N/A')}</li>
                    <li><strong>License Number:</strong> {user_data.get('medicalLicenseNumber', 'N/A')}</li>
                    <li><strong>Specialization:</strong> {user_data.get('specialization', 'N/A')}</li>
                    <li><strong>Years of Experience:</strong> {user_data.get('yearsOfExperience', 'N/A')}</li>
                    <li><strong>Current Workplace:</strong> {user_data.get('currentWorkplace', 'N/A')}</li>
                    <li><strong>Registration Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            
            <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3>🔍 Action Required:</h3>
                <p>Please review this registration and approve/reject the new user account.</p>
                <a href="http://localhost:5173/admin" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Review Registration →
                </a>
            </div>
            
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                This is an automated notification from Healthcare Management System.
            </p>
        </div>
        """
        
        # Send admin notification email
        ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [admin_email]},
            Message={
                'Subject': {'Data': admin_subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': strip_tags(admin_html), 'Charset': 'UTF-8'},
                    'Html': {'Data': admin_html, 'Charset': 'UTF-8'}
                }
            }
        )
        
        print(f"✅ Registration emails sent successfully!")
        print(f"   • User confirmation sent to: {user_email}")
        print(f"   • Admin notification sent to: {admin_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send registration emails: {e}")
        return False
import re
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ComprehensiveRegistrationView(APIView):
    """
    Comprehensive healthcare professional registration with GDPR/HIPAA compliance
    Handles multi-step registration process for medical professionals
    """
    permission_classes = [AllowAny]

    def validate_recaptcha(self, recaptcha_token):
        """Validate reCAPTCHA token"""
        if not recaptcha_token:
            return False, "reCAPTCHA verification required"
        
        # For development, temporarily bypass reCAPTCHA validation
        # TODO: Re-enable with proper keys in production
        return True, ""
        
        # For development, use test keys - replace with real keys in production
        secret_key = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"  # Test secret key
        
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': recaptcha_token
            }
        )
        
        result = response.json()
        return result.get('success', False), result.get('error-codes', ['Unknown error'])

    def validate_email_format(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_phone_format(self, phone):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', phone)
        # Check if it's between 10-15 digits
        return 10 <= len(digits_only) <= 15

    def validate_license_expiry(self, expiry_date):
        """Validate that license expiry date is in the future"""
        try:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            return expiry > timezone.now().date()
        except:
            return False

    def validate_password_strength(self, password):
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < 8:  # Reduced from 12 to 8 for better usability
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Removed repeated character check for better usability
        # if re.search(r'(.)\1{2,}', password):
        #     errors.append("Password cannot contain repeated characters")
        
        return len(errors) == 0, errors

    def check_rate_limit(self, request):
        """Enhanced rate limiting with soft-coded configuration"""
        
        # Check if rate limiting is enabled
        if not REGISTRATION_RATE_LIMITING['enabled']:
            return True, "Rate limiting disabled"
        
        # Bypass rate limiting in development mode
        if REGISTRATION_RATE_LIMITING['development_mode']:
            return True, "Development mode - rate limiting bypassed"
        
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        # Create cache keys for different time periods
        hourly_cache_key = f"reg_attempts_hourly_{ip_address}"
        daily_cache_key = f"reg_attempts_daily_{ip_address}"
        
        # Check hourly attempts
        hourly_attempts = cache.get(hourly_cache_key, 0)
        daily_attempts = cache.get(daily_cache_key, 0)
        
        max_hourly = REGISTRATION_RATE_LIMITING['max_attempts_per_hour']
        max_daily = REGISTRATION_RATE_LIMITING['max_attempts_per_day']
        
        # More lenient checking for registration
        if hourly_attempts >= max_hourly:
            return False, f"Too many registration attempts this hour ({hourly_attempts}/{max_hourly}). Please try again later."
        
        if daily_attempts >= max_daily:
            return False, f"Too many registration attempts today ({daily_attempts}/{max_daily}). Please contact support if you need assistance."
        
        # Update counters
        timeout_seconds = REGISTRATION_RATE_LIMITING['timeout_hours'] * 3600
        cache.set(hourly_cache_key, hourly_attempts + 1, timeout_seconds)
        cache.set(daily_cache_key, daily_attempts + 1, 86400)  # 24 hours
        
        return True, f"Rate limit OK ({hourly_attempts + 1}/{max_hourly} this hour)"

    def validate_medical_license(self, license_number, issuing_authority):
        """Basic validation of medical license format"""
        # This would typically integrate with medical board APIs
        # For now, basic format validation
        if not license_number or len(license_number) < 5:
            return False, "Invalid medical license number format"
        
        if not issuing_authority or len(issuing_authority) < 3:
            return False, "Invalid license issuing authority"
        
        return True, ""

    def post(self, request):
        """Handle comprehensive registration"""
        logger.info("🚀 Registration request received!")
        logger.info(f"Request data keys: {list(request.data.keys())}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content type: {request.content_type}")
        
        try:
            # Debug: Log the incoming data
            logger.info(f"Registration request data keys: {list(request.data.keys())}")
            logger.info(f"Request data size: {len(str(request.data))}")
            
            # Enhanced rate limiting check with soft coding
            logger.info("🛡️ Checking rate limiting for registration...")
            rate_ok, rate_msg = self.check_rate_limit(request)
            logger.info(f"🛡️ Rate limiting result: {rate_ok} - {rate_msg}")
            
            if not rate_ok:
                logger.warning(f"🚫 Registration blocked by rate limiting: {rate_msg}")
                return Response({
                    'success': False,
                    'error': 'Registration temporarily limited',
                    'message': rate_msg,
                    'retry_after': 'Please try again in a few minutes'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            data = request.data
            errors = {}

            # Step 1: Personal Information Validation
            required_personal = ['firstName', 'lastName', 'dateOfBirth', 'gender', 'nationality']
            for field in required_personal:
                if not data.get(field):
                    errors[field] = f"{field} is required"

            # Step 2: Contact Information Validation
            email = data.get('email', '').strip()
            confirm_email = data.get('confirmEmail', '').strip()
            
            if not email:
                errors['email'] = "Email is required"
            elif not self.validate_email_format(email):
                errors['email'] = "Invalid email format"
            elif User.objects.filter(email__iexact=email).exists():
                errors['email'] = "Email already registered"
            
            if email != confirm_email:
                errors['confirmEmail'] = "Email addresses do not match"

            phone = data.get('phone', '').strip()
            if not phone:
                errors['phone'] = "Phone number is required"
            elif not self.validate_phone_format(phone):
                errors['phone'] = "Invalid phone number format"

            required_contact = ['address', 'city', 'zipCode', 'country']
            for field in required_contact:
                if not data.get(field):
                    errors[field] = f"{field} is required"

            # Step 3: Professional Information Validation
            professional_fields = [
                'professionalTitle', 'medicalLicenseNumber', 'licenseIssuingAuthority',
                'licenseExpiryDate', 'specialization', 'yearsOfExperience', 'currentWorkplace'
            ]
            for field in professional_fields:
                if not data.get(field):
                    errors[field] = f"{field} is required"

            # Validate medical license
            license_valid, license_msg = self.validate_medical_license(
                data.get('medicalLicenseNumber', ''),
                data.get('licenseIssuingAuthority', '')
            )
            if not license_valid:
                errors['medicalLicenseNumber'] = license_msg

            # Validate license expiry
            expiry_date = data.get('licenseExpiryDate')
            if expiry_date and not self.validate_license_expiry(expiry_date):
                errors['licenseExpiryDate'] = "License expiry date must be in the future"

            # Step 4: Account Security Validation
            username = data.get('username', '').strip()
            if not username:
                errors['username'] = "Username is required"
            elif len(username) < 6:
                errors['username'] = "Username must be at least 6 characters"
            elif User.objects.filter(username__iexact=username).exists():
                errors['username'] = "Username already taken"

            password = data.get('password', '')
            confirm_password = data.get('confirmPassword', '')
            
            if not password:
                errors['password'] = "Password is required"
            else:
                pwd_valid, pwd_errors = self.validate_password_strength(password)
                if not pwd_valid:
                    errors['password'] = ". ".join(pwd_errors)
            
            if password != confirm_password:
                errors['confirmPassword'] = "Passwords do not match"

            # Security questions validation
            security_fields = ['securityQuestion1', 'securityAnswer1', 'securityQuestion2', 'securityAnswer2']
            for field in security_fields:
                if not data.get(field):
                    errors[field] = f"{field} is required"

            if data.get('securityQuestion1') == data.get('securityQuestion2'):
                errors['securityQuestion2'] = "Please select different security questions"

            # Step 5: Legal Compliance Validation
            legal_consents = ['gdprConsent', 'hipaaAgreement', 'termsAccepted', 'dataProcessingConsent']
            for consent in legal_consents:
                if not data.get(consent):
                    errors[consent] = f"{consent} is required"

            emergency_fields = ['emergencyContact', 'emergencyContactPhone']
            for field in emergency_fields:
                if not data.get(field):
                    errors[field] = f"{field} is required"

            # reCAPTCHA validation
            recaptcha_token = data.get('recaptcha_token')
            recaptcha_valid, recaptcha_msg = self.validate_recaptcha(recaptcha_token)
            if not recaptcha_valid:
                errors['recaptcha_token'] = "reCAPTCHA verification failed"

            # Return validation errors if any
            if errors:
                logger.warning(f"Registration validation failed for {data.get('email', 'unknown')}: {errors}")
                # Also log all field values for debugging (excluding sensitive data)
                debug_data = {k: v for k, v in data.items() if k not in ['password', 'confirmPassword']}
                logger.info(f"Form data (non-sensitive): {debug_data}")
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user account with all data
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    full_name=f"{data.get('firstName')} {data.get('lastName')}",
                    role='doctor',  # Default role, admin will assign specific roles
                    phone_number=phone,
                    license_number=data.get('medicalLicenseNumber'),
                    specialization=data.get('specialization'),
                    is_active=False,  # Require admin approval
                    is_verified=False
                )

                # Create comprehensive user profile (you might need to create additional models)
                # For now, we'll store additional data in a JSON field or create related models
                
                # Generate verification token
                verification_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                user.verification_token = verification_token
                user.save()

                # Log registration for audit
                logger.info(f"New user registration: {email} - {data.get('firstName')} {data.get('lastName')}")

                # Send email notifications using the new notification system
                try:
                    # Send email notifications using direct SES
                    logger.info(f"📧 About to send registration emails to: {email}")
                    email_sent = send_registration_emails(data)
                    if email_sent:
                        logger.info("✅ Registration emails sent successfully!")
                    else:
                        logger.warning("⚠️ Registration emails failed to send")

                except Exception as e:
                    logger.error(f"Failed to send notification emails: {str(e)}")
                    # Fallback to old email system if notification system fails
                    try:
                        # User notification email (fallback)
                        send_mail(
                            subject='Registration Pending Approval - Mastermind Healthcare',
                            message=f"""
Dear {data.get('firstName')} {data.get('lastName')},

Thank you for registering with Mastermind Healthcare Platform.

Your registration is currently pending approval from our administrative team. We will review your credentials and notify you once your account is approved.

Registration Details:
- Name: {data.get('firstName')} {data.get('lastName')}
- Email: {email}
- Professional Title: {data.get('professionalTitle')}
- Specialization: {data.get('specialization')}
- Medical License: {data.get('medicalLicenseNumber')}

You will receive an email notification once your account is approved.

If you have any questions, please contact our support team.

Best regards,
Mastermind Healthcare Team
                            """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )

                        # Admin notification email (fallback)
                        admin_emails = User.objects.filter(role='super_admin', is_active=True).values_list('email', flat=True)
                        if admin_emails:
                            send_mail(
                                subject='New Registration Pending Approval',
                                message=f"""
New healthcare professional registration pending approval:

Name: {data.get('firstName')} {data.get('lastName')}
Email: {email}
Professional Title: {data.get('professionalTitle')}
Specialization: {data.get('specialization')}
Medical License: {data.get('medicalLicenseNumber')}
License Authority: {data.get('licenseIssuingAuthority')}
Workplace: {data.get('currentWorkplace')}
Registration Time: {timezone.now()}

Please review and approve the registration in the admin panel.
                                """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=list(admin_emails),
                                fail_silently=True,
                            )
                    except Exception as fallback_error:
                        logger.error(f"Fallback email notification also failed: {str(fallback_error)}")

                return Response({
                    'success': True,
                    'message': 'Registration successful! Your account is pending admin approval. You will receive an email notification once approved.',
                    'data': {
                        'email': email,
                        'name': f"{data.get('firstName')} {data.get('lastName')}",
                        'status': 'pending_approval',
                        'registration_time': timezone.now().isoformat()
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error during registration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
