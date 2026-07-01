#!/usr/bin/env python
"""
Database check script to see what doctor and user data exists
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from django.contrib.auth import get_user_model
from medicine.models import Doctor
from hospital.models import CustomUser

User = get_user_model()  # This will get the correct user model

def check_database():
    print("=" * 50)
    print("DATABASE CONTENT ANALYSIS")
    print("=" * 50)
    
    # Check Users (Custom User model)
    print("\n🔍 ALL USERS:")
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    for user in users[:10]:
        print(f"  - ID: {user.id}, Email: {user.email}, Role: {getattr(user, 'role', 'N/A')}")
        print(f"    Name: {getattr(user, 'full_name', 'N/A')}, Active: {user.is_active}")
        print(f"    Staff: {user.is_staff}, Admin: {user.is_superuser}")
    
    # Check Doctors
    print("\n🏥 DOCTORS:")
    doctors = Doctor.objects.all()
    print(f"Total doctors: {doctors.count()}")
    for doctor in doctors[:10]:
        print(f"  - ID: {doctor.id}, User: {doctor.user.email if doctor.user else 'No User'}")
        print(f"    Specialization: {doctor.specialization}, Experience: {doctor.years_experience} years")
        print(f"    License: {doctor.license_number}, Fee: ${doctor.consultation_fee}")
    
    # Check what user data is available for profile
    print("\n👤 SAMPLE USER PROFILE DATA:")
    if users.exists():
        sample_user = users.first()
        print(f"Sample User: {sample_user.email}")
        print(f"  - ID: {sample_user.id}")
        print(f"  - Email: {sample_user.email}")
        print(f"  - Full Name: {getattr(sample_user, 'full_name', 'N/A')}")
        print(f"  - Role: {getattr(sample_user, 'role', 'N/A')}")
        print(f"  - Phone: {getattr(sample_user, 'phone_number', 'N/A')}")
        print(f"  - Is Staff: {sample_user.is_staff}")
        print(f"  - Is Superuser: {sample_user.is_superuser}")
        print(f"  - Date Joined: {getattr(sample_user, 'date_joined', 'N/A')}")
        
        # Check if user has doctor profile
        try:
            doctor_profile = sample_user.doctor_profile
            print(f"  - Has Doctor Profile: Yes")
            print(f"    Specialization: {doctor_profile.specialization}")
            print(f"    Experience: {doctor_profile.years_experience}")
            print(f"    License: {doctor_profile.license_number}")
            print(f"    Bio: {doctor_profile.bio[:100]}...")
        except Exception as e:
            print(f"  - Has Doctor Profile: No ({e})")
    
    print("\n" + "=" * 50)
    print("RECOMMENDATION:")
    print("=" * 50)
    
    if doctors.count() == 0:
        print("❌ No doctors found in database!")
        print("📝 Need to create sample doctor profiles")
    elif users.count() == 0:
        print("❌ No users found in database!")
        print("📝 Need to create user accounts")
    else:
        print("✅ Database has user/doctor data")
        print("📊 Doctor profile can fetch real data from backend")

if __name__ == "__main__":
    check_database()
