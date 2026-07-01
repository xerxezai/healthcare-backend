from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Patient, Doctor

@receiver(post_save, sender=User)
def create_or_update_patient_profile(sender, instance, created, **kwargs):
    """Auto-create patient profile for new users if needed"""
    pass  # Implement as needed

@receiver(post_save, sender=User)
def create_or_update_doctor_profile(sender, instance, created, **kwargs):
    """Auto-create doctor profile for new users if needed"""
    pass  # Implement as needed
