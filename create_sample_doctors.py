#!/usr/bin/env python
"""
Create sample doctor profiles for testing
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
from decimal import Decimal

User = get_user_model()

def create_sample_doctors():
    print("Creating sample doctor profiles...")
    
    # Get users with doctor role
    doctor_users = User.objects.filter(role='doctor')
    print(f"Found {doctor_users.count()} users with doctor role")
    
    # Create doctor profiles for existing doctor users
    sample_doctors_data = [
        {
            'license_number': 'MD001234',
            'specialization': 'cardiology',
            'qualification': 'MD',
            'years_experience': 12,
            'education': 'MBBS from Delhi Medical College, MD in Cardiology from AIIMS',
            'certifications': 'Board Certified Cardiologist, Fellow of American College of Cardiology',
            'hospital_affiliation': 'City General Hospital, Heart Care Center',
            'consultation_fee': Decimal('2500.00'),
            'is_available_emergency': True,
            'bio': 'Experienced cardiologist with 12+ years in treating heart conditions. Specialized in interventional cardiology and preventive heart care.'
        },
        {
            'license_number': 'MD005678',
            'specialization': 'neurology',
            'qualification': 'MD',
            'years_experience': 8,
            'education': 'MBBS from Grant Medical College, MD in Neurology from Tata Institute',
            'certifications': 'Board Certified Neurologist, Epilepsy Specialist Certification',
            'hospital_affiliation': 'Neuro Science Institute, Brain Care Hospital',
            'consultation_fee': Decimal('3000.00'),
            'is_available_emergency': True,
            'bio': 'Neurologist specializing in brain disorders, epilepsy, and stroke management. Committed to advanced neurological care.'
        }
    ]
    
    created_count = 0
    for i, doctor_user in enumerate(doctor_users):
        # Check if doctor profile already exists
        if hasattr(doctor_user, 'doctor_profile'):
            print(f"Doctor profile already exists for {doctor_user.email}")
            continue
            
        # Use sample data if available, otherwise generate
        if i < len(sample_doctors_data):
            doctor_data = sample_doctors_data[i]
        else:
            doctor_data = {
                'license_number': f'MD{str(doctor_user.id).zfill(6)}',
                'specialization': 'general',
                'qualification': 'MBBS',
                'years_experience': 5,
                'education': 'MBBS from Medical College',
                'certifications': 'Board Certified Physician',
                'hospital_affiliation': 'General Hospital',
                'consultation_fee': Decimal('1500.00'),
                'is_available_emergency': False,
                'bio': f'General physician with experience in primary healthcare. Email: {doctor_user.email}'
            }
        
        # Update user's full name if empty
        if not doctor_user.full_name:
            if i == 0:
                doctor_user.full_name = "Dr. Sarah Johnson"
            elif i == 1:
                doctor_user.full_name = "Dr. Michael Chen"
            else:
                doctor_user.full_name = f"Dr. Physician {i+1}"
            doctor_user.save()
        
        # Create doctor profile
        try:
            doctor_profile = Doctor.objects.create(
                user=doctor_user,
                **doctor_data
            )
            print(f"✅ Created doctor profile for {doctor_user.email} ({doctor_user.full_name})")
            print(f"   Specialization: {doctor_profile.get_specialization_display()}")
            print(f"   License: {doctor_profile.license_number}")
            created_count += 1
        except Exception as e:
            print(f"❌ Error creating doctor profile for {doctor_user.email}: {e}")
    
    print(f"\n✅ Created {created_count} doctor profiles")
    
    # Verify creation
    total_doctors = Doctor.objects.count()
    print(f"📊 Total doctors in database: {total_doctors}")
    
    # Show all doctors
    print("\n🏥 ALL DOCTORS:")
    for doctor in Doctor.objects.all():
        print(f"  - {doctor.user.full_name} ({doctor.user.email})")
        print(f"    Specialization: {doctor.get_specialization_display()}")
        print(f"    Experience: {doctor.years_experience} years")
        print(f"    License: {doctor.license_number}")
        print()

if __name__ == "__main__":
    create_sample_doctors()
