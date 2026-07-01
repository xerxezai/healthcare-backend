#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print('=== USER CLEANUP OPERATION ===')
print('Target: Delete all users EXCEPT mastermind@xerxez.com')
print()

# Find the super admin to preserve
super_admin = User.objects.filter(email='mastermind@xerxez.com').first()

if not super_admin:
    print('❌ ERROR: Super admin mastermind@xerxez.com not found!')
    print('Operation aborted for safety.')
    exit(1)

print(f'✅ Super admin found: {super_admin.username} ({super_admin.email})')
print(f'   ID: {super_admin.id}')
print()

# Get all users except the super admin
users_to_delete = User.objects.exclude(email='mastermind@xerxez.com')
total_to_delete = users_to_delete.count()

print(f'Users to be deleted: {total_to_delete}')
print()

if total_to_delete == 0:
    print('✅ No users to delete. Database is already clean.')
    exit(0)

# Show users that will be deleted
print('=== USERS TO BE DELETED ===')
for i, user in enumerate(users_to_delete, 1):
    print(f'{i:2d}. ID: {user.id:2d} | {user.username:20s} | {user.email:30s} | {getattr(user, "full_name", "N/A")}')

print()
print('⚠️  WARNING: This operation cannot be undone!')
print('⚠️  All user data, profiles, and related records will be permanently deleted!')
print()

# Confirmation
confirm = input('Type "DELETE ALL USERS" to confirm this operation: ')

if confirm == "DELETE ALL USERS":
    print()
    print('🗑️  Starting deletion process...')
    
    deleted_count = 0
    errors = []
    
    for user in users_to_delete:
        try:
            user_info = f"ID:{user.id} {user.username} ({user.email})"
            user.delete()
            deleted_count += 1
            print(f'✅ Deleted: {user_info}')
        except Exception as e:
            error_msg = f"❌ Failed to delete {user_info}: {str(e)}"
            errors.append(error_msg)
            print(error_msg)
    
    print()
    print('=== CLEANUP SUMMARY ===')
    print(f'✅ Successfully deleted: {deleted_count} users')
    print(f'❌ Failed deletions: {len(errors)}')
    
    if errors:
        print()
        print('=== ERRORS ===')
        for error in errors:
            print(error)
    
    # Verify remaining users
    remaining_users = User.objects.all()
    print()
    print('=== REMAINING USERS ===')
    for user in remaining_users:
        print(f'ID: {user.id} | {user.username} | {user.email} | {getattr(user, "full_name", "N/A")}')
    
    print()
    print(f'🎉 Cleanup completed! {remaining_users.count()} user(s) remaining in database.')
    
    if remaining_users.count() == 1 and remaining_users.first().email == 'mastermind@xerxez.com':
        print('✅ Perfect! Only the super admin remains.')
    else:
        print('⚠️  Warning: More than expected users remain.')

else:
    print()
    print('❌ Operation cancelled. No users were deleted.')
    print('   (You must type exactly "DELETE ALL USERS" to confirm)')
