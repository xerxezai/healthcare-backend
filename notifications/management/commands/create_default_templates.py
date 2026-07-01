# backend/notifications/management/commands/create_default_templates.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create default notification templates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username of the admin user to set as template creator'
        )
    
    def handle(self, *args, **options):
        admin_username = options['admin_username']
        
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
        
        templates = [
            {
                'name': 'Appointment Reminder',
                'template_type': 'appointment_reminder',
                'email_subject': 'Appointment Reminder - {{appointment_date}}',
                'email_body_text': '''Dear {{patient_name}},

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
                'email_body_html': '''<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #007bff;">Appointment Reminder</h2>
    
    <p>Dear <strong>{{patient_name}}</strong>,</p>
    
    <p>This is a friendly reminder about your upcoming appointment:</p>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Date:</strong> {{appointment_date}}</p>
        <p><strong>Time:</strong> {{appointment_time}}</p>
        <p><strong>Doctor:</strong> {{doctor_name}}</p>
        <p><strong>Clinic:</strong> {{clinic_name}}</p>
        <p><strong>Address:</strong> {{clinic_address}}</p>
    </div>
    
    <p>Please arrive 15 minutes early for check-in.</p>
    
    <p><em>If you need to reschedule or cancel, please contact us at least 24 hours in advance.</em></p>
    
    <p>Best regards,<br>
    <strong>{{clinic_name}} Team</strong></p>
</body>
</html>''',
                'sms_message': 'Reminder: You have an appointment on {{appointment_date}} at {{appointment_time}} with {{doctor_name}} at {{clinic_name}}. Please arrive 15 minutes early.',
                'available_variables': ['patient_name', 'appointment_date', 'appointment_time', 'doctor_name', 'clinic_name', 'clinic_address']
            },
            {
                'name': 'Test Results Available',
                'template_type': 'test_results',
                'email_subject': 'Your Test Results Are Ready',
                'email_body_text': '''Dear {{patient_name}},

Your {{test_name}} results are now available for review.

You can view your results by logging into your patient portal or by visiting our clinic.

Results URL: {{results_url}}

If you have any questions about your results, please don't hesitate to contact us.

Best regards,
{{clinic_name}} Team''',
                'email_body_html': '''<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #28a745;">Test Results Available</h2>
    
    <p>Dear <strong>{{patient_name}}</strong>,</p>
    
    <p>Your <strong>{{test_name}}</strong> results are now available for review.</p>
    
    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
        <p>You can view your results by logging into your patient portal or by visiting our clinic.</p>
        <p><a href="{{results_url}}" style="color: #007bff; text-decoration: none;">View Results</a></p>
    </div>
    
    <p>If you have any questions about your results, please don't hesitate to contact us.</p>
    
    <p>Best regards,<br>
    <strong>{{clinic_name}} Team</strong></p>
</body>
</html>''',
                'sms_message': 'Your {{test_name}} results are ready. Please log into your patient portal or visit our clinic to review them. {{clinic_name}}',
                'available_variables': ['patient_name', 'test_name', 'results_url', 'clinic_name']
            },
            {
                'name': 'Emergency Alert',
                'template_type': 'emergency_alert',
                'email_subject': 'URGENT: Emergency Alert',
                'email_body_text': '''EMERGENCY ALERT

{{emergency_message}}

Time: {{timestamp}}

Please take immediate action as required.

This is an automated emergency notification.''',
                'email_body_html': '''<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <h1 style="margin: 0; color: white;">🚨 EMERGENCY ALERT</h1>
    </div>
    
    <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545;">
        <p><strong>{{emergency_message}}</strong></p>
        <p><strong>Time:</strong> {{timestamp}}</p>
    </div>
    
    <p><strong>Please take immediate action as required.</strong></p>
    
    <p><em>This is an automated emergency notification.</em></p>
</body>
</html>''',
                'sms_message': 'EMERGENCY: {{emergency_message}} - {{timestamp}}',
                'available_variables': ['emergency_message', 'timestamp']
            },
            {
                'name': 'Appointment Confirmation',
                'template_type': 'appointment_confirmation',
                'email_subject': 'Appointment Confirmed - {{appointment_date}}',
                'email_body_text': '''Dear {{patient_name}},

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
                'email_body_html': '''<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #28a745;">✅ Appointment Confirmed</h2>
    
    <p>Dear <strong>{{patient_name}}</strong>,</p>
    
    <p>Your appointment has been confirmed:</p>
    
    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
        <p><strong>Date:</strong> {{appointment_date}}</p>
        <p><strong>Time:</strong> {{appointment_time}}</p>
        <p><strong>Doctor:</strong> {{doctor_name}}</p>
        <p><strong>Clinic:</strong> {{clinic_name}}</p>
        <p><strong>Address:</strong> {{clinic_address}}</p>
    </div>
    
    <p>Please save this confirmation for your records.</p>
    
    <p>We look forward to seeing you!</p>
    
    <p>Best regards,<br>
    <strong>{{clinic_name}} Team</strong></p>
</body>
</html>''',
                'sms_message': 'Appointment confirmed: {{appointment_date}} at {{appointment_time}} with {{doctor_name}} at {{clinic_name}}.',
                'available_variables': ['patient_name', 'appointment_date', 'appointment_time', 'doctor_name', 'clinic_name', 'clinic_address']
            },
            {
                'name': 'Prescription Ready',
                'template_type': 'prescription_ready',
                'email_subject': 'Your Prescription is Ready for Pickup',
                'email_body_text': '''Dear {{patient_name}},

Your prescription is ready for pickup at our pharmacy.

Prescription: {{prescription_name}}
Pharmacy: {{pharmacy_name}}
{{pharmacy_address}}

Pharmacy Hours: {{pharmacy_hours}}

Please bring a valid ID when picking up your prescription.

Best regards,
{{clinic_name}} Team''',
                'email_body_html': '''<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #007bff;">💊 Prescription Ready</h2>
    
    <p>Dear <strong>{{patient_name}}</strong>,</p>
    
    <p>Your prescription is ready for pickup at our pharmacy.</p>
    
    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
        <p><strong>Prescription:</strong> {{prescription_name}}</p>
        <p><strong>Pharmacy:</strong> {{pharmacy_name}}</p>
        <p><strong>Address:</strong> {{pharmacy_address}}</p>
        <p><strong>Hours:</strong> {{pharmacy_hours}}</p>
    </div>
    
    <p>Please bring a valid ID when picking up your prescription.</p>
    
    <p>Best regards,<br>
    <strong>{{clinic_name}} Team</strong></p>
</body>
</html>''',
                'sms_message': 'Your prescription {{prescription_name}} is ready for pickup at {{pharmacy_name}}. Please bring valid ID.',
                'available_variables': ['patient_name', 'prescription_name', 'pharmacy_name', 'pharmacy_address', 'pharmacy_hours', 'clinic_name']
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults={**template_data, 'created_by': admin_user}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created template: {template.name}')
                )
            else:
                # Update existing template
                for key, value in template_data.items():
                    if key != 'template_type':
                        setattr(template, key, value)
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Updated template: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Template creation completed!'
                f'\n📝 Created: {created_count} templates'
                f'\n🔄 Updated: {updated_count} templates'
            )
        )
