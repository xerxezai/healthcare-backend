"""
Management command to create or update a super admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hospital.models import StaffProfile, AdminPermissions
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update a super admin user'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email for the super admin')
        parser.add_argument('--password', type=str, help='Password for the super admin')
        parser.add_argument('--name', type=str, help='Full name for the super admin')
    
    def handle(self, *args, **options):
        email = options.get('email') or 'mastermind@xerxez.in'
        password = options.get('password') or 'password123'
        name = options.get('name') or 'Super Administrator'
        
        self.stdout.write(f'Setting up super admin user: {email}')
        
        # Check if user already exists
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'User {email} already exists. Updating to super admin...')
            
            # Update user to super admin
            user.role = 'super_admin'
            user.is_staff = True
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.save()
            
        except User.DoesNotExist:
            self.stdout.write(f'Creating new super admin user: {email}')
            
            # Create new super admin user
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=name,
                role='super_admin',
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
        
        # Ensure staff profile exists
        staff_profile, created = StaffProfile.objects.get_or_create(
            user=user,
            defaults={
                'department': 'Administration',
                'position': 'Super Administrator',
                'join_date': timezone.now().date(),
                'phone_number': user.phone_number or ''
            }
        )
        
        if created:
            self.stdout.write('Created staff profile')
        
        # Ensure admin permissions exist with full access
        admin_permissions, created = AdminPermissions.objects.get_or_create(
            user=user,
            defaults={
                'can_manage_users': True,
                'can_view_reports': True,
                'can_manage_departments': True,
                'can_access_billing': True,
                'can_manage_inventory': True,
                'can_access_emergency': True,
            }
        )
        
        if not created:
            # Update existing permissions to ensure full access
            admin_permissions.can_manage_users = True
            admin_permissions.can_view_reports = True
            admin_permissions.can_manage_departments = True
            admin_permissions.can_access_billing = True
            admin_permissions.can_manage_inventory = True
            admin_permissions.can_access_emergency = True
            admin_permissions.save()
            self.stdout.write('Updated admin permissions')
        else:
            self.stdout.write('Created admin permissions')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Super admin user setup completed successfully!\n'
                f'Email: {email}\n'
                f'Password: {password}\n'
                f'Role: {user.role}\n'
                f'Is Staff: {user.is_staff}\n'
                f'Is Superuser: {user.is_superuser}'
            )
        )
