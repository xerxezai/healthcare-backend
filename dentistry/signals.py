from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Patient, Dentist

@receiver(post_save, sender=User)
def create_dental_profiles(sender, instance, created, **kwargs):
    """
    Automatically create dental profiles when users are created
    """
    if created:
        # Check if user should be a dentist (you can add logic here)
        # For now, we'll just create patient profiles for all users
        if not hasattr(instance, 'dental_patient'):
            # Generate patient ID
            patient_count = Patient.objects.count() + 1
            patient_id = f"PAT{patient_count:06d}"
            
            Patient.objects.create(
                user=instance,
                patient_id=patient_id,
                date_of_birth='1990-01-01',  # Default, should be updated
                phone='',
                emergency_contact='',
                emergency_phone=''
            )
