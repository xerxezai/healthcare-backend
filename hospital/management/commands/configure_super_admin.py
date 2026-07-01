"""
Configure super admin with full permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.models import AdminDashboardFeatures

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure super admin with full permissions'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email of the super admin to configure')
    
    def handle(self, *args, **options):
        email = options.get('email') or 'mastermind@xerxez.in'
        
        try:
            user = User.objects.get(email=email)
            
            if user.role != 'super_admin':
                self.stdout.write(self.style.ERROR(f'User {email} is not a super admin'))
                return
                
            self.stdout.write(f'Configuring super admin: {user.email}')
            
            # Create or update dashboard features with full access
            features, created = AdminDashboardFeatures.objects.get_or_create(
                user=user,
                defaults={
                    'user_management': True,
                    'patient_management': True,
                    'doctor_management': True,
                    'nurse_management': True,
                    'pharmacist_management': True,
                    'medicine_module': True,
                    'dentistry_module': True,
                    'dermatology_module': True,
                    'pathology_module': True,
                    'radiology_module': True,
                    'homeopathy_module': True,
                    'allopathy_module': True,
                    'dna_sequencing_module': True,
                    'secureneat_module': True,
                    'subscription_management': True,
                    'billing_reports': True,
                    'financial_dashboard': True,
                    'system_settings': True,
                    'audit_logs': True,
                    'user_analytics': True,
                    'medical_reports': True,
                    'revenue_reports': True,
                    'appointment_analytics': True,
                    'inventory_reports': True,
                    'create_user': True,
                    'schedule_appointment': True,
                    'generate_report': True,
                    'backup_system': True,
                    'send_notifications': True,
                }
            )
            
            if not created:
                # Update existing features to full access
                features.user_management = True
                features.patient_management = True
                features.doctor_management = True
                features.nurse_management = True
                features.pharmacist_management = True
                features.medicine_module = True
                features.dentistry_module = True
                features.dermatology_module = True
                features.pathology_module = True
                features.radiology_module = True
                features.homeopathy_module = True
                features.allopathy_module = True
                features.dna_sequencing_module = True
                features.secureneat_module = True
                features.subscription_management = True
                features.billing_reports = True
                features.financial_dashboard = True
                features.system_settings = True
                features.audit_logs = True
                features.user_analytics = True
                features.medical_reports = True
                features.revenue_reports = True
                features.appointment_analytics = True
                features.inventory_reports = True
                features.create_user = True
                features.schedule_appointment = True
                features.generate_report = True
                features.backup_system = True
                features.send_notifications = True
                features.save()
                
            self.stdout.write(self.style.SUCCESS('✅ Super admin configured with full access to all modules:'))
            self.stdout.write('  🏥 Doctor Management: ✅')
            self.stdout.write('  💊 Medicine Module: ✅')
            self.stdout.write('  🦷 Dentistry Module: ✅')
            self.stdout.write('  🌿 Homeopathy Module: ✅')
            self.stdout.write('  💉 Allopathy Module: ✅')
            self.stdout.write('  🧬 DNA Sequencing Module: ✅')
            self.stdout.write('  🔒 SecureNeat Module: ✅')
            self.stdout.write('  📊 All Management Features: ✅')
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Super admin with email {email} not found'))
