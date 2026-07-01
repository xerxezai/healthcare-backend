#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print('=== ALL SUPERUSERS ===')
superusers = User.objects.filter(is_superuser=True)

if superusers.exists():
    for user in superusers:
        print(f'ID: {user.id}')
        print(f'Username: {user.username}')
        print(f'Email: {user.email}')
        print(f'Full Name: {getattr(user, "full_name", "N/A")}')
        print(f'Phone: {getattr(user, "phone_number", "N/A")}')
        print(f'Role: {getattr(user, "role", "N/A")}')
        print(f'Is Active: {user.is_active}')
        print(f'Is Staff: {user.is_staff}')
        print(f'Is Superuser: {user.is_superuser}')
        print(f'Date Joined: {user.date_joined}')
        print(f'Last Login: {user.last_login}')
        print('=' * 50)
else:
    print('No superusers found!')

print(f'Total Superusers: {superusers.count()}')

print('\n=== ALL STAFF USERS ===')
staff_users = User.objects.filter(is_staff=True)

if staff_users.exists():
    for user in staff_users:
        print(f'ID: {user.id}')
        print(f'Username: {user.username}')
        print(f'Email: {user.email}')
        print(f'Full Name: {getattr(user, "full_name", "N/A")}')
        print(f'Role: {getattr(user, "role", "N/A")}')
        print(f'Is Active: {user.is_active}')
        print(f'Is Staff: {user.is_staff}')
        print(f'Is Superuser: {user.is_superuser}')
        print('---')
else:
    print('No staff users found!')

print(f'Total Staff Users: {staff_users.count()}')

print('\n=== ALL USERS WITH ADMIN-LIKE ROLES ===')
admin_role_users = User.objects.filter(role__icontains='admin')

if admin_role_users.exists():
    for user in admin_role_users:
        print(f'ID: {user.id}')
        print(f'Username: {user.username}')
        print(f'Email: {user.email}')
        print(f'Full Name: {getattr(user, "full_name", "N/A")}')
        print(f'Role: {getattr(user, "role", "N/A")}')
        print(f'Is Active: {user.is_active}')
        print(f'Is Staff: {user.is_staff}')
        print(f'Is Superuser: {user.is_superuser}')
        print('---')
else:
    print('No users with admin roles found!')

print(f'Total Admin Role Users: {admin_role_users.count()}')

print('\n=== TOTAL USER SUMMARY ===')
total_users = User.objects.count()
active_users = User.objects.filter(is_active=True).count()
print(f'Total Users in Database: {total_users}')
print(f'Active Users: {active_users}')
print(f'Inactive Users: {total_users - active_users}')
