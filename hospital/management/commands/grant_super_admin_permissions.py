# backend/hospital/management/commands/grant_super_admin_permissions.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Command(BaseCommand):
    help = 'Grant full read/write permissions to super administrator'

    def handle(self, *args, **options):
        """
        Grant comprehensive permissions to the super administrator
        """
        super_admin_email = 'mastermind@xerxez.com'
        
        try:
            # Get the super admin user
            super_admin = User.objects.get(email=super_admin_email)
            
            self.stdout.write(f"🔑 Granting comprehensive permissions to {super_admin_email}...")
            
            # Ensure super admin has superuser status
            super_admin.is_superuser = True
            super_admin.is_staff = True
            super_admin.is_active = True
            super_admin.role = 'super_admin'
            super_admin.save()
            
            # Get or create super admin group
            super_admin_group, created = Group.objects.get_or_create(name='Super Administrators')
            if created:
                self.stdout.write("✅ Created Super Administrators group")
            
            # Get all permissions
            all_permissions = Permission.objects.all()
            
            # Add all permissions to the super admin group
            super_admin_group.permissions.set(all_permissions)
            
            # Add super admin to the group
            super_admin.groups.add(super_admin_group)
            
            # Grant all individual permissions directly to super admin
            super_admin.user_permissions.set(all_permissions)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully granted {all_permissions.count()} permissions to {super_admin_email}")
            )
            
            # Log the specific capabilities granted
            capabilities = [
                "Full Django Admin Access",
                "All Model CRUD Operations", 
                "User Management",
                "Subscription Management",
                "Medical Records Access",
                "System Configuration",
                "API Access (All Endpoints)",
                "Database Operations",
                "Security Management",
                "Backup and Recovery"
            ]
            
            self.stdout.write("\n🎯 Super Admin Capabilities Granted:")
            for capability in capabilities:
                self.stdout.write(f"   ✅ {capability}")
                
            # Create summary
            self.stdout.write(f"\n📊 Permission Summary:")
            self.stdout.write(f"   👤 User: {super_admin.email}")
            self.stdout.write(f"   🔐 Role: {super_admin.role}")
            self.stdout.write(f"   🌟 Superuser: {super_admin.is_superuser}")
            self.stdout.write(f"   👥 Groups: {super_admin.groups.count()}")
            self.stdout.write(f"   🔑 Individual Permissions: {super_admin.user_permissions.count()}")
            self.stdout.write(f"   🛡️ Group Permissions: {super_admin_group.permissions.count()}")
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Super Administrator permissions successfully configured!")
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Super admin user {super_admin_email} not found. Please create the user first.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error granting permissions: {str(e)}")
            )
