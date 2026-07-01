from django.core.management.base import BaseCommand
from hospital.models import CustomUser, AdminDashboardFeatures

class Command(BaseCommand):
    help = 'Verify and fix medicine module access for tameem@gmail.com'

    def handle(self, *args, **options):
        try:
            # Get the user
            user = CustomUser.objects.get(email='tameem@gmail.com')
            self.stdout.write(f'👤 Found user: {user.email}')
            
            # Get or create dashboard features
            features, created = AdminDashboardFeatures.objects.get_or_create(user=user)
            
            if created:
                self.stdout.write('✨ Created new dashboard features for tameem@gmail.com')
            
            # Ensure medicine module is enabled
            features.medicine_module = True
            # Ensure other modules are properly set (disable unauthorized ones)
            features.doctor_management = False
            features.dentistry_module = False
            features.dermatology_module = False
            features.pathology_module = False
            features.radiology_module = False
            features.homeopathy_module = False
            features.allopathy_module = False
            features.dna_sequencing_module = False
            features.secureneat_module = False
            features.save()
            
            self.stdout.write('✅ Medicine module access verified and fixed!')
            self.stdout.write('')
            self.stdout.write('📋 tameem@gmail.com permissions:')
            self.stdout.write(f'  🏥 Medicine Module: {"✅" if features.medicine_module else "❌"}')
            self.stdout.write(f'  👨‍⚕️ Doctor Management: {"✅" if features.doctor_management else "❌"}')
            self.stdout.write(f'  🦷 Dentistry: {"✅" if features.dentistry_module else "❌"}')
            self.stdout.write(f'  🩺 Dermatology: {"✅" if features.dermatology_module else "❌"}')
            self.stdout.write(f'  🧪 Pathology: {"✅" if features.pathology_module else "❌"}')
            self.stdout.write(f'  📡 Radiology: {"✅" if features.radiology_module else "❌"}')
            self.stdout.write('')
            self.stdout.write('🎯 Next steps:')
            self.stdout.write('  1. Login as tameem@gmail.com (password: password123)')
            self.stdout.write('  2. Go to http://localhost:5173/')
            self.stdout.write('  3. Check the LEFT SIDEBAR for "Medicine" module')
            self.stdout.write('  4. The Medicine module should be visible with these sub-options:')
            self.stdout.write('     - Dashboard')
            self.stdout.write('     - General Medicine')
            self.stdout.write('     - Emergency Medicine')
            self.stdout.write('     - Diabetes Patient Tracker')
            self.stdout.write('     - Diabetic Retinopathy AI')
            
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ User tameem@gmail.com not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
