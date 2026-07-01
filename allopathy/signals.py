from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import AllopathyFile, AllopathyAnalysis, AllopathyPatientS3
import boto3
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AllopathyFile)
def handle_file_upload(sender, instance, created, **kwargs):
    """Handle post-save operations for file uploads"""
    if created:
        logger.info(f"New allopathy file uploaded: {instance.original_name}")
        
        # Update file status to processing if it's a medical document
        medical_categories = ['lab_results', 'radiology', 'pathology']
        if instance.category in medical_categories:
            instance.status = 'processing'
            instance.save()
            
            # Trigger automatic analysis
            trigger_automatic_analysis(instance)

@receiver(pre_delete, sender=AllopathyFile)
def cleanup_s3_file(sender, instance, **kwargs):
    """Clean up S3 file when model instance is deleted"""
    try:
        s3_client = boto3.client('s3')
        s3_client.delete_object(Bucket=instance.s3_bucket, Key=instance.s3_key)
        logger.info(f"Deleted S3 file: {instance.s3_key}")
    except Exception as e:
        logger.error(f"Failed to delete S3 file {instance.s3_key}: {str(e)}")

@receiver(post_save, sender=AllopathyAnalysis)
def handle_analysis_completion(sender, instance, created, **kwargs):
    """Handle analysis completion and notifications"""
    if not created and instance.status == 'completed':
        logger.info(f"Analysis completed for patient: {instance.patient.full_name}")
        
        # Update related file status
        if instance.file:
            instance.file.status = 'analyzed'
            instance.file.save()
        
        # Check if follow-up is required
        if instance.follow_up_required and instance.follow_up_date:
            # Here you could trigger notifications or scheduling
            logger.info(f"Follow-up required for {instance.patient.full_name} on {instance.follow_up_date}")

@receiver(post_save, sender=AllopathyPatientS3)
def handle_patient_admission(sender, instance, created, **kwargs):
    """Handle patient admission and status changes"""
    if created:
        logger.info(f"New patient admitted: {instance.full_name}")
        
        # Initialize vital signs if not provided
        if not instance.vital_signs:
            instance.vital_signs = {
                'temperature': None,
                'blood_pressure': None,
                'heart_rate': None,
                'respiratory_rate': None,
                'oxygen_saturation': None,
                'recorded_at': timezone.now().isoformat()
            }
            instance.save()

def trigger_automatic_analysis(file_instance):
    """Trigger automatic analysis for uploaded medical files"""
    try:
        # Determine analysis type based on file category
        analysis_type_mapping = {
            'lab_results': 'lab_analysis',
            'radiology': 'radiology_analysis',
            'pathology': 'pathology_detection',
        }
        
        analysis_type = analysis_type_mapping.get(file_instance.category)
        if analysis_type:
            AllopathyAnalysis.objects.create(
                hospital=file_instance.hospital,
                patient=file_instance.patient,
                file=file_instance,
                analysis_type=analysis_type,
                input_data={'file_id': str(file_instance.id)},
                confidence_score=0.0,  # Will be updated after processing
                status='pending'
            )
            logger.info(f"Triggered {analysis_type} for file: {file_instance.original_name}")
    
    except Exception as e:
        logger.error(f"Failed to trigger automatic analysis: {str(e)}")

# Custom signal for real-time notifications
from django.dispatch import Signal

# Define custom signals
analysis_completed = Signal()
critical_result_detected = Signal()
patient_status_changed = Signal()

@receiver(analysis_completed)
def handle_analysis_completed_notification(sender, analysis, **kwargs):
    """Handle notifications when analysis is completed"""
    # Here you could integrate with notification services
    logger.info(f"Analysis completed notification: {analysis.analysis_type} for {analysis.patient.full_name}")

@receiver(critical_result_detected)
def handle_critical_result(sender, analysis, **kwargs):
    """Handle critical results that require immediate attention"""
    logger.warning(f"Critical result detected: {analysis.analysis_type} for {analysis.patient.full_name}")
    
    # Update analysis to high priority
    analysis.follow_up_required = True
    analysis.follow_up_date = timezone.now().date()
    analysis.save()

@receiver(patient_status_changed)
def handle_patient_status_change(sender, patient, old_status, new_status, **kwargs):
    """Handle patient status changes"""
    logger.info(f"Patient {patient.full_name} status changed from {old_status} to {new_status}")
    
    # If patient is discharged, archive related files
    if new_status == 'discharged':
        patient.files.filter(status='uploaded').update(status='archived')
