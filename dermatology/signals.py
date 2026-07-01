from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import DermatologyConsultation, DiagnosticProcedure, TreatmentPlan, SkinPhoto
import uuid


@receiver(pre_save, sender=DermatologyConsultation)
def generate_consultation_number(sender, instance, **kwargs):
    """Generate unique consultation number if not provided"""
    if not instance.consultation_number:
        # Generate consultation number with format: DERM-YYYY-XXXXXX
        year = timezone.now().year
        # Get the last consultation number for this year
        last_consultation = DermatologyConsultation.objects.filter(
            consultation_number__startswith=f'DERM-{year}-'
        ).order_by('-consultation_number').first()
        
        if last_consultation:
            # Extract the sequence number and increment
            last_sequence = int(last_consultation.consultation_number.split('-')[-1])
            new_sequence = last_sequence + 1
        else:
            new_sequence = 1
        
        instance.consultation_number = f'DERM-{year}-{new_sequence:06d}'


@receiver(pre_save, sender=DiagnosticProcedure)
def generate_procedure_number(sender, instance, **kwargs):
    """Generate unique procedure number if not provided"""
    if not instance.procedure_number:
        # Generate procedure number with format: PROC-YYYY-XXXXXX
        year = timezone.now().year
        last_procedure = DiagnosticProcedure.objects.filter(
            procedure_number__startswith=f'PROC-{year}-'
        ).order_by('-procedure_number').first()
        
        if last_procedure:
            last_sequence = int(last_procedure.procedure_number.split('-')[-1])
            new_sequence = last_sequence + 1
        else:
            new_sequence = 1
        
        instance.procedure_number = f'PROC-{year}-{new_sequence:06d}'


@receiver(post_save, sender=DermatologyConsultation)
def consultation_status_change(sender, instance, created, **kwargs):
    """Handle consultation status changes"""
    if not created:
        # If consultation is completed, check if follow-up is needed
        if instance.status == 'completed' and instance.next_appointment_recommended:
            # Could trigger notification system here
            pass
        
        # If consultation is started, record start time
        if instance.status == 'in_progress' and not instance.actual_start_time:
            instance.actual_start_time = timezone.now()
            # Avoid infinite loop by using update instead of save
            DermatologyConsultation.objects.filter(id=instance.id).update(
                actual_start_time=instance.actual_start_time
            )


@receiver(post_save, sender=TreatmentPlan)
def treatment_plan_created(sender, instance, created, **kwargs):
    """Handle new treatment plan creation"""
    if created:
        # Could trigger notifications to patient or care team
        # Could schedule follow-up reminders
        pass


@receiver(post_save, sender=SkinPhoto)
def skin_photo_uploaded(sender, instance, created, **kwargs):
    """Handle new skin photo upload"""
    if created:
        # Could trigger automatic AI analysis request
        # Could generate thumbnail if not provided
        pass
