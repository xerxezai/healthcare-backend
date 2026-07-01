"""
Final comprehensive security test for all modules and all admin users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.models import AdminDashboardFeatures

User = get_user_model()


class Command(BaseCommand):
    help = 'Final comprehensive security test for all admin users'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔒 COMPREHENSIVE SECURITY AUDIT'))
        self.stdout.write('=' * 60)
        
        # Get all admin and super_admin users
        admin_users = User.objects.filter(role__in=['admin', 'super_admin'])
        
        if not admin_users.exists():
            self.stdout.write(self.style.WARNING('No admin users found'))
            return
        
        self.stdout.write(f'Found {admin_users.count()} admin users to audit\n')
        
        # Define all modules for security check
        all_modules = {
            'doctor_management': 'Doctor Management',
            'medicine_module': 'Medicine Module', 
            'dentistry_module': 'Dentistry Module',
            'dermatology_module': 'Dermatology Module',
            'pathology_module': 'Pathology Module',
            'radiology_module': 'Radiology Module',
            'homeopathy_module': 'Homeopathy Module',
            'allopathy_module': 'Allopathy Module',
            'dna_sequencing_module': 'DNA Sequencing Module',
            'secureneat_module': 'SecureNeat Module',
        }
        
        # High risk modules (sensitive data)
        high_risk_modules = [
            'doctor_management', 'dna_sequencing_module'
        ]
        
        for user in admin_users:
            self.stdout.write(f'👤 {user.email}')
            self.stdout.write(f'   Role: {user.role}')
            
            try:
                features = AdminDashboardFeatures.objects.get(user=user)
                
                # Check module access
                enabled_modules = []
                for field, name in all_modules.items():
                    if hasattr(features, field) and getattr(features, field):
                        enabled_modules.append(name)
                
                if enabled_modules:
                    self.stdout.write(f'   📋 Enabled Modules: {", ".join(enabled_modules)}')
                    
                    # Security analysis
                    high_risk_count = 0
                    for field in high_risk_modules:
                        if hasattr(features, field) and getattr(features, field):
                            high_risk_count += 1
                    
                    if high_risk_count > 0:
                        self.stdout.write(f'   ⚠️  High Risk Modules: {high_risk_count} enabled')
                    
                    # Role-based validation
                    if user.role == 'super_admin':
                        self.stdout.write(self.style.SUCCESS('   ✅ Super Admin: Full access authorized'))
                    else:
                        # Regular admin should have limited access
                        if len(enabled_modules) == 1:
                            self.stdout.write(self.style.SUCCESS(f'   ✅ Limited Access: Only {enabled_modules[0]}'))
                        elif len(enabled_modules) > 1:
                            self.stdout.write(self.style.WARNING(f'   ⚠️  Multiple Modules: {len(enabled_modules)} enabled - Review needed'))
                else:
                    self.stdout.write('   📋 Enabled Modules: None')
                    if user.role == 'admin':
                        self.stdout.write(self.style.ERROR('   ❌ Admin user with no module access'))
                        
            except AdminDashboardFeatures.DoesNotExist:
                self.stdout.write(self.style.ERROR('   ❌ No dashboard features configured'))
            
            self.stdout.write('')  # Empty line
        
        # Summary recommendations
        self.stdout.write('🛡️  SECURITY RECOMMENDATIONS:')
        self.stdout.write('1. Regular admins should have minimal, specific module access')
        self.stdout.write('2. High-risk modules (Doctor, DNA) require special authorization')
        self.stdout.write('3. Review users with multiple module access')
        self.stdout.write('4. Ensure all admin users have dashboard features configured')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🔒 Security audit complete'))
