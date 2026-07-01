# Management command to create default notification templates
# This command sets up the basic templates needed for healthcare notifications

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.notification_models import NotificationTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default notification templates for healthcare notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username of the admin user to set as template creator'
        )
        
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing templates with new content'
        )
    
    def handle(self, *args, **options):
        admin_username = options['admin_username']
        update_existing = options['update_existing']
        
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            # Try to get any superuser
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No admin user found. Please create a superuser first.')
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(f'Using superuser: {admin_user.username}')
                )
        
        templates = [
            {
                'template_type': 'appointment_reminder',
                'subject_template': 'Appointment Reminder - {{appointment_date}}',
                'email_template': '''Dear {{patient_name}},

This is a friendly reminder about your upcoming appointment:

Date: {{appointment_date}}
Time: {{appointment_time}}
Doctor: {{doctor_name}}
Clinic: {{clinic_name}}
{{clinic_address}}

Please arrive 15 minutes early for check-in.

If you need to reschedule or cancel, please contact us at least 24 hours in advance.

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Reminder: You have an appointment on {{appointment_date}} at {{appointment_time}} with {{doctor_name}} at {{clinic_name}}. Please arrive 15 minutes early.',
                'is_active': True
            },
            {
                'template_type': 'test_results',
                'subject_template': 'Your Test Results Are Ready',
                'email_template': '''Dear {{patient_name}},

Your {{test_name}} results are now available for review.

You can view your results by logging into your patient portal or by visiting our clinic.

{% if results_url %}Results URL: {{results_url}}{% endif %}

If you have any questions about your results, please don't hesitate to contact us.

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Your {{test_name}} results are ready. Please log into your patient portal or visit our clinic to review them. {{clinic_name}}',
                'is_active': True
            },
            {
                'template_type': 'emergency_alert',
                'subject_template': 'URGENT: Emergency Alert',
                'email_template': '''EMERGENCY ALERT

{{emergency_message}}

Time: {{timestamp}}

Please take immediate action as required.

This is an automated emergency notification.''',
                'sms_template': 'EMERGENCY: {{emergency_message}} - {{timestamp}}',
                'is_active': True
            },
            {
                'template_type': 'appointment_confirmation',
                'subject_template': 'Appointment Confirmed - {{appointment_date}}',
                'email_template': '''Dear {{patient_name}},

Your appointment has been confirmed:

Date: {{appointment_date}}
Time: {{appointment_time}}
Doctor: {{doctor_name}}
Clinic: {{clinic_name}}
{{clinic_address}}

Please save this confirmation for your records.

We look forward to seeing you!

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Appointment confirmed: {{appointment_date}} at {{appointment_time}} with {{doctor_name}} at {{clinic_name}}.',
                'is_active': True
            },
            {
                'template_type': 'prescription_ready',
                'subject_template': 'Your Prescription is Ready for Pickup',
                'email_template': '''Dear {{patient_name}},

Your prescription is ready for pickup at our pharmacy.

Prescription: {{prescription_name}}
Pharmacy: {{pharmacy_name}}
{{pharmacy_address}}

Pharmacy Hours: {{pharmacy_hours}}

Please bring a valid ID when picking up your prescription.

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Your prescription {{prescription_name}} is ready for pickup at {{pharmacy_name}}. Please bring valid ID.',
                'is_active': True
            },
            {
                'template_type': 'registration_confirmation',
                'subject_template': 'Welcome to {{clinic_name}} - Registration Confirmation',
                'email_template': '''Dear {{patient_name}},

Welcome to {{clinic_name}}! Your registration has been completed successfully.

Account Details:
- Email: {{patient_email}}
- Registration Date: {{registration_date}}

You can now access our patient portal and schedule appointments online.

If you have any questions, please don't hesitate to contact us.

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Welcome to {{clinic_name}}! Your registration is complete. You can now access our patient portal.',
                'is_active': True
            },
            {
                'template_type': 'password_reset',
                'subject_template': 'Password Reset Request - {{clinic_name}}',
                'email_template': '''Dear {{patient_name}},

You have requested to reset your password for your {{clinic_name}} account.

To reset your password, please click the link below:
{{reset_link}}

This link will expire in 24 hours for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
{{clinic_name}} Team''',
                'sms_template': 'Your password reset code for {{clinic_name}}: {{reset_code}}. This code expires in 15 minutes.',
                'is_active': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for template_data in templates:
            template_type = template_data['template_type']
            
            try:
                template = NotificationTemplate.objects.get(template_type=template_type)
                
                if update_existing:
                    # Update existing template
                    for key, value in template_data.items():
                        setattr(template, key, value)
                    template.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Updated template: {template_type}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⏭️  Skipped existing template: {template_type} (use --update-existing to update)')
                    )
                
            except NotificationTemplate.DoesNotExist:
                # Create new template
                NotificationTemplate.objects.create(**template_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created template: {template_type}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Template setup completed!'
                f'\n📝 Created: {created_count} templates'
                f'\n🔄 Updated: {updated_count} templates'
                f'\n⏭️  Skipped: {skipped_count} templates'
            )
        )
        
        # Show usage examples
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.HTTP_INFO(
                    '\n📋 Usage Examples:'
                    '\n  - Appointment reminder: POST /api/hospital/notifications/appointment-reminder/'
                    '\n  - Test results: POST /api/hospital/notifications/test-results/'
                    '\n  - Emergency alert: POST /api/hospital/notifications/emergency-alert/'
                    '\n  - Enhanced notification: POST /api/hospital/notifications/enhanced/send/'
                    '\n  - Bulk notifications: POST /api/hospital/notifications/bulk/'
                )
            )
