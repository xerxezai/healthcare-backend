from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact_form(request):
    """
    Handle contact form submissions with AWS SES integration
    """
    try:
        data = request.data
        
        # Extract form data
        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        department = data.get('department', '')
        country = data.get('country', '')
        contact_method = data.get('contactMethod', '')
        subject = data.get('subject', '')
        message = data.get('message', '')
        newsletter = data.get('newsletter', False)
        
        # Basic validation
        if not all([name, email, phone, subject, message]):
            return Response({
                'success': False,
                'error': 'All required fields must be filled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare email context for the contact notification
        email_context = {
            'contact_name': name,
            'contact_email': email,
            'contact_phone': phone,
            'department': department,
            'country': country,
            'contact_method': contact_method,
            'subject': subject,
            'message': message,
            'newsletter_signup': newsletter,
            'platform_name': getattr(settings, 'PLATFORM_NAME', 'Healthcare Platform'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@xerxez.in'),
            'timestamp': data.get('timestamp', 'N/A')
        }
        
        # Send notification to support team
        support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@xerxez.in')
        admin_emails = getattr(settings, 'ADMIN_EMAIL_LIST', [support_email])
        
        try:
            # Render email templates
            try:
                admin_html_content = render_to_string('notifications/email/contact_form_submission.html', email_context)
            except Exception as template_error:
                logger.warning(f"Could not load admin email template: {template_error}")
                admin_html_content = f"""
                <h2>New Contact Form Submission</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Department:</strong> {department}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong> {message}</p>
                """
            
            # Send to support team using Django's send_mail
            try:
                admin_sent = send_mail(
                    subject=f'New Contact Form Submission: {subject}',
                    message=f'New contact form submission from {name} ({email})\n\nSubject: {subject}\n\nMessage: {message}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@xerxez.in'),
                    recipient_list=admin_emails,
                    html_message=admin_html_content,
                    fail_silently=False
                )
                logger.info(f"Admin email sent successfully: {admin_sent}")
            except Exception as admin_email_error:
                logger.error(f"Failed to send admin email: {admin_email_error}")
                admin_sent = 0
            
            # Send confirmation to user
            confirmation_context = {
                'user_name': name,
                'subject': subject,
                'platform_name': getattr(settings, 'PLATFORM_NAME', 'Healthcare Platform'),
                'support_email': support_email,
                'expected_response_time': '24 hours'
            }
            
            try:
                user_html_content = render_to_string('notifications/email/contact_form_confirmation.html', confirmation_context)
            except Exception as template_error:
                logger.warning(f"Could not load user email template: {template_error}")
                user_html_content = f"""
                <h2>Thank You, {name}!</h2>
                <p>We've received your inquiry about "{subject}" and will respond within 24 hours.</p>
                <p>Best regards,<br>{getattr(settings, 'PLATFORM_NAME', 'Healthcare Platform')}</p>
                """
            
            try:
                user_sent = send_mail(
                    subject=f'Thank you for contacting us - {subject}',
                    message=f'Thank you for contacting us, {name}. We will respond within 24 hours.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@xerxez.in'),
                    recipient_list=[email],
                    html_message=user_html_content,
                    fail_silently=False
                )
                logger.info(f"User confirmation email sent successfully: {user_sent}")
            except Exception as user_email_error:
                logger.error(f"Failed to send user confirmation email: {user_email_error}")
                user_sent = 0
            
            logger.info(f"Contact form submitted successfully by {email}")
            
            return Response({
                'success': True,
                'message': 'Your message has been sent successfully. We will respond within 24 hours.',
                'admin_notification_sent': bool(admin_sent),
                'user_confirmation_sent': bool(user_sent)
            }, status=status.HTTP_200_OK)
            
        except Exception as email_error:
            logger.error(f"Email sending failed: {str(email_error)}")
            # Still return success to user, but log the email failure
            return Response({
                'success': True,
                'message': 'Your message has been received. We will respond within 24 hours.',
                'note': 'Email notification may be delayed due to technical issues.'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Contact form submission error: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred while processing your request. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
