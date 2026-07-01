#!/usr/bin/env python
"""
Healthcare Module Permission Management Utility
This script helps manage user permissions for healthcare modules dynamically.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from hospital.models import CustomUser, AdminDashboardFeatures
from django.core.management.base import BaseCommand

class PermissionManager:
    """Manages healthcare module permissions for users"""
    
    AVAILABLE_MODULES = [
        'medicine_module',
        'dentistry_module', 
        'dermatology_module',
        'pathology_module',
        'radiology_module',
        'homeopathy_module',
        'allopathy_module',
        'cosmetology_module',
        'dna_sequencing_module',
        'secureneat_module'
    ]
    
    @classmethod
    def get_user_permissions(cls, email):
        """Get current permissions for a user"""
        try:
            user = CustomUser.objects.get(email=email)
            features, _ = AdminDashboardFeatures.objects.get_or_create(user=user)
            
            permissions = {}
            for module in cls.AVAILABLE_MODULES:
                permissions[module] = getattr(features, module, False)
                
            return user, features, permissions
        except CustomUser.DoesNotExist:
            return None, None, None
    
    @classmethod
    def set_user_permissions(cls, email, enabled_modules=None, disabled_modules=None):
        """Set specific permissions for a user"""
        if enabled_modules is None:
            enabled_modules = []
        if disabled_modules is None:
            disabled_modules = []
            
        try:
            user = CustomUser.objects.get(email=email)
            features, created = AdminDashboardFeatures.objects.get_or_create(user=user)
            
            # Enable specified modules
            for module in enabled_modules:
                if module in cls.AVAILABLE_MODULES:
                    setattr(features, module, True)
                    
            # Disable specified modules  
            for module in disabled_modules:
                if module in cls.AVAILABLE_MODULES:
                    setattr(features, module, False)
                    
            features.save()
            
            return True, f"Permissions updated for {email}"
        except CustomUser.DoesNotExist:
            return False, f"User {email} not found"
        except Exception as e:
            return False, f"Error updating permissions: {str(e)}"
    
    @classmethod
    def grant_only_modules(cls, email, modules):
        """Grant access to only specified modules (disable all others)"""
        try:
            user = CustomUser.objects.get(email=email)
            features, created = AdminDashboardFeatures.objects.get_or_create(user=user)
            
            # First disable all modules
            for module in cls.AVAILABLE_MODULES:
                setattr(features, module, False)
                
            # Then enable only specified modules
            for module in modules:
                if module in cls.AVAILABLE_MODULES:
                    setattr(features, module, True)
                    
            features.save()
            
            return True, f"Granted access to {modules} for {email}"
        except CustomUser.DoesNotExist:
            return False, f"User {email} not found"
        except Exception as e:
            return False, f"Error updating permissions: {str(e)}"
    
    @classmethod
    def list_all_users_permissions(cls):
        """List permissions for all users"""
        users_permissions = []
        
        for user in CustomUser.objects.all():
            features, _ = AdminDashboardFeatures.objects.get_or_create(user=user)
            
            enabled_modules = []
            for module in cls.AVAILABLE_MODULES:
                if getattr(features, module, False):
                    enabled_modules.append(module.replace('_module', '').title())
                    
            users_permissions.append({
                'email': user.email,
                'name': user.get_full_name() or user.username,
                'role': user.role,
                'enabled_modules': enabled_modules
            })
            
        return users_permissions
    
    @classmethod
    def create_test_scenarios(cls):
        """Create test scenarios for different user types"""
        scenarios = {
            'full_access_admin': cls.AVAILABLE_MODULES,
            'clinical_staff': ['medicine_module', 'pathology_module', 'radiology_module'],
            'specialist': ['dermatology_module', 'cosmetology_module'],
            'researcher': ['dna_sequencing_module', 'pathology_module'],
            'student': ['secureneat_module', 'medicine_module']
        }
        return scenarios

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python permission_manager.py <command> [args]")
        print("Commands:")
        print("  list - List all user permissions")
        print("  get <email> - Get permissions for specific user") 
        print("  grant <email> <modules> - Grant only specified modules")
        print("  scenarios - Show test scenarios")
        return
        
    command = sys.argv[1]
    pm = PermissionManager()
    
    if command == 'list':
        users = pm.list_all_users_permissions()
        print("\n=== USER PERMISSIONS ===")
        for user in users:
            print(f"\n📧 {user['email']} ({user['role']})")
            print(f"   Name: {user['name']}")
            print(f"   Modules: {', '.join(user['enabled_modules']) if user['enabled_modules'] else 'None'}")
            
    elif command == 'get' and len(sys.argv) > 2:
        email = sys.argv[2]
        user, features, permissions = pm.get_user_permissions(email)
        if user:
            print(f"\n=== PERMISSIONS FOR {email} ===")
            for module, enabled in permissions.items():
                status = "✅" if enabled else "❌"
                print(f"{status} {module.replace('_module', '').title()}")
        else:
            print(f"❌ User {email} not found")
            
    elif command == 'grant' and len(sys.argv) > 3:
        email = sys.argv[2]
        modules = [f"{module}_module" for module in sys.argv[3].split(',')]
        success, message = pm.grant_only_modules(email, modules)
        print("✅" if success else "❌", message)
        
    elif command == 'scenarios':
        scenarios = pm.create_test_scenarios()
        print("\n=== TEST SCENARIOS ===")
        for scenario_name, modules in scenarios.items():
            print(f"\n{scenario_name.title().replace('_', ' ')}:")
            for module in modules:
                print(f"  - {module.replace('_module', '').title()}")

if __name__ == "__main__":
    main()
