"""
Comprehensive security verification script
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.models import AdminDashboardFeatures, AdminPermissions

User = get_user_model()


class Command(BaseCommand):
    help = 'Comprehensive security verification for all admin users'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔒 Security Verification Report'))
        self.stdout.write('=' * 50)
        
        # Get all admin users
        admin_users = User.objects.filter(role='admin')
        
        for user in admin_users:
            self.stdout.write(f'\n👤 User: {user.email}')
            self.stdout.write(f'   Role: {user.role}')
            
            try:
                features = AdminDashboardFeatures.objects.get(user=user)
                
                # Check medical modules
                enabled_modules = []
                if features.medicine_module:
                    enabled_modules.append('Medicine')
                if features.radiology_module:
                    enabled_modules.append('Radiology')
                if features.dentistry_module:
                    enabled_modules.append('Dentistry')
                if features.dermatology_module:
                    enabled_modules.append('Dermatology')
                if features.pathology_module:
                    enabled_modules.append('Pathology')
                
                if enabled_modules:
                    self.stdout.write(f'   📋 Enabled Modules: {", ".join(enabled_modules)}')
                else:
                    self.stdout.write('   📋 Enabled Modules: None')
                
                # Security validation
                if user.email == 'tameem@gmail.com':
                    # Tameem should only have medicine
                    if features.medicine_module and not any([
                        features.radiology_module, features.dentistry_module,
                        features.dermatology_module, features.pathology_module
                    ]):
                        self.stdout.write(self.style.SUCCESS('   ✅ Security: CORRECT - Only medicine access'))
                    else:
                        self.stdout.write(self.style.ERROR('   ❌ Security: VIOLATION - Unauthorized module access'))
                        
                # Check admin permissions
                try:
                    permissions = AdminPermissions.objects.get(user=user)
                    if permissions.can_manage_users and user.role == 'admin':
                        self.stdout.write('   🔐 User Management: Enabled')
                except AdminPermissions.DoesNotExist:
                    self.stdout.write('   🔐 Admin Permissions: Not configured')
                    
            except AdminDashboardFeatures.DoesNotExist:
                self.stdout.write('   📋 Dashboard Features: Not configured')
        
        # Super admin check
        super_admins = User.objects.filter(role='super_admin')
        if super_admins.exists():
            self.stdout.write(f'\n👑 Super Admins: {super_admins.count()} found')
            for sa in super_admins:
                self.stdout.write(f'   - {sa.email}')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  No super admin users found'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🔒 Security verification complete'))
