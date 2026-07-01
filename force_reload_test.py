#!/usr/bin/env python
"""
Force Reload and Test Notification System
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import importlib

def force_reload_and_test():
    """Force reload the notification system and test"""
    print("🔄 Force Reloading Notification System")
    print("="*50)
    
    try:
        # Import and reload the module
        import hospital.notification_system as ns
        importlib.reload(ns)
        
        print("✅ Module reloaded successfully")
        
        # Check what's available
        print(f"📋 Available classes: {[name for name in dir(ns) if name[0].isupper()]}")
        print(f"📋 Available functions: {[name for name in dir(ns) if name.startswith('send_')]}")
        
        # Check the notification_manager
        if hasattr(ns, 'notification_manager'):
            manager = ns.notification_manager
            print(f"Manager type: {type(manager)}")
            
            if manager:
                print(f"Manager methods: {[m for m in dir(manager) if not m.startswith('_')]}")
                
                if hasattr(manager, 'send_admin_account_created_notification'):
                    print("✅ Found send_admin_account_created_notification method!")
                    return manager
                else:
                    print("❌ Method not found in manager")
            else:
                print("❌ Manager is None")
        else:
            print("❌ notification_manager not found")
            
        # Try creating a new instance
        if hasattr(ns, 'HealthcareNotificationManager'):
            print("✅ Creating new HealthcareNotificationManager instance...")
            manager = ns.HealthcareNotificationManager()
            
            if hasattr(manager, 'send_admin_account_created_notification'):
                print("✅ New instance has the required method!")
                return manager
            else:
                print("❌ New instance missing the method")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    return None

if __name__ == "__main__":
    manager = force_reload_and_test()
    
    if manager:
        print("\n🎉 Notification system is working!")
        
        # Test with sample data
        print("\n🧪 Testing admin notification function...")
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create test user objects (don't save)
        test_admin = User(
            email='test@example.com',
            full_name='Test Admin',
            role='admin'
        )
        
        test_creator = User(
            email='creator@example.com',
            full_name='Test Creator',
            role='super_admin'
        )
        
        try:
            result = manager.send_admin_account_created_notification(
                admin_user=test_admin,
                temp_password='TestPass123!',
                created_by_user=test_creator
            )
            
            print(f"✅ Test result: {result}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
    else:
        print("\n❌ Still not working. Need to check the file manually.")
