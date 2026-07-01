"""
Management command to check and fix user dashboard permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.models import AdminDashboardFeatures

User = get_user_model()


class Command(BaseCommand):
    help = 'Check and fix user dashboard permissions'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email of the user to check')
        parser.add_argument('--fix', action='store_true', help='Fix permissions if incorrect')
    
    def handle(self, *args, **options):
        email = options.get('email') or 'tameem@gmail.com'
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'Checking permissions for user: {user.email}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            
            # Check dashboard features
            features, created = AdminDashboardFeatures.objects.get_or_create(
                user=user,
                defaults={
                    'user_management': False,
                    'patient_management': False,
                    'doctor_management': False,
                    'nurse_management': False,
                    'pharmacist_management': False,
                    'medicine_module': True,  # Only medicine for Tameem
                    'dentistry_module': False,
                    'dermatology_module': False,
                    'pathology_module': False,
                    'radiology_module': False,  # Should be FALSE for Tameem
                    'subscription_management': False,
                    'billing_reports': False,
                    'financial_dashboard': False,
                    'system_settings': False,
                    'audit_logs': False,
                }
            )
            
            if created:
                self.stdout.write('Created dashboard features for user')
            
            self.stdout.write('\nCurrent Dashboard Features:')
            self.stdout.write(f'  User Management: {features.user_management}')
            self.stdout.write(f'  Patient Management: {features.patient_management}')
            self.stdout.write(f'  Medicine Module: {features.medicine_module}')
            self.stdout.write(f'  Radiology Module: {features.radiology_module}')
            self.stdout.write(f'  Dentistry Module: {features.dentistry_module}')
            self.stdout.write(f'  Dermatology Module: {features.dermatology_module}')
            self.stdout.write(f'  Pathology Module: {features.pathology_module}')
            
            # Check if permissions need fixing
            if options.get('fix') or features.radiology_module or features.dentistry_module or features.dermatology_module or features.pathology_module:
                self.stdout.write('\n🔧 Fixing permissions for Tameem (only medicine access)...')
                
                features.user_management = False
                features.patient_management = False
                features.doctor_management = False
                features.nurse_management = False
                features.pharmacist_management = False
                features.medicine_module = True  # Only this should be True
                features.dentistry_module = False
                features.dermatology_module = False
                features.pathology_module = False
                features.radiology_module = False  # This should be FALSE
                features.subscription_management = False
                features.billing_reports = False
                features.financial_dashboard = False
                features.system_settings = False
                features.audit_logs = False
                features.save()
                
                self.stdout.write(self.style.SUCCESS('✅ Permissions fixed! Tameem now has access to ONLY medicine module'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Permissions are correctly configured'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
