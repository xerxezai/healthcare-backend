from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PathologyOrder, PathologyOrderTest, PathologyReport, Specimen


@receiver(post_save, sender=PathologyOrderTest)
def update_order_total_cost(sender, instance, **kwargs):
    """Update total cost when order tests are added/modified"""
    order = instance.order
    total_cost = sum(ot.cost for ot in order.pathologyordertest_set.all())
    order.total_cost = total_cost
    order.save(update_fields=['total_cost'])


@receiver(post_save, sender=PathologyReport)
def update_order_test_status(sender, instance, created, **kwargs):
    """Update order test status based on report status"""
    if not created and instance.status == 'finalized':
        instance.order_test.status = 'completed'
        instance.order_test.completed_at = timezone.now()
        instance.order_test.save(update_fields=['status', 'completed_at'])


@receiver(post_save, sender=Specimen)
def update_order_status_on_specimen_collection(sender, instance, created, **kwargs):
    """Update order status when specimen is collected"""
    if instance.status == 'collected':
        order = instance.order
        if order.status == 'pending':
            order.status = 'collected'
            order.collection_date = instance.collection_datetime
            order.save(update_fields=['status', 'collection_date'])


@receiver(pre_save, sender=PathologyOrder)
def set_expected_completion(sender, instance, **kwargs):
    """Set expected completion time based on tests"""
    if instance.pk and instance.status == 'processing':
        # Calculate expected completion based on longest processing time
        max_processing_time = 0
        for order_test in instance.pathologyordertest_set.all():
            if order_test.test.processing_time_hours > max_processing_time:
                max_processing_time = order_test.test.processing_time_hours
        
        if max_processing_time > 0:
            from datetime import timedelta
            instance.expected_completion = timezone.now() + timedelta(hours=max_processing_time)


@receiver(post_save, sender=PathologyReport)
def send_critical_result_notification(sender, instance, **kwargs):
    """Send notification for critical results"""
    if instance.result_status == 'critical' and instance.status == 'finalized':
        try:
            # Import here to avoid circular imports
            from hospital.notification_system import notification_manager
            
            # Get patient data
            patient = instance.order_test.order.patient
            patient_data = {
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'patient_id': patient.patient_id,
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
                'phone': patient.phone,
                'emergency_contact': getattr(patient, 'emergency_contact', 'Not available')
            }
            
            # Get lab data
            lab_data = {
                'test_name': instance.order_test.test.name,
                'order_id': instance.order_test.order.order_id,
                'test_date': instance.order_test.order.created_at.strftime('%Y-%m-%d'),
                'report_date': instance.finalized_at.strftime('%Y-%m-%d %H:%M') if instance.finalized_at else '',
                'result_timestamp': instance.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'critical_summary': f"{instance.order_test.test.name}: Critical values detected",
                'critical_results': [
                    {
                        'parameter': instance.order_test.test.name,
                        'value': 'Critical',
                        'unit': '',
                        'reference_range': 'See detailed report'
                    }
                ],
                'chart_url': f"/pathology/reports/{instance.id}/"
            }
            
            # Get physician data from the order
            physician = instance.order_test.order.ordered_by if hasattr(instance.order_test.order, 'ordered_by') else None
            if physician:
                physician_data = {
                    'name': f"Dr. {physician.user.first_name} {physician.user.last_name}",
                    'email': physician.user.email,
                    'phone': getattr(physician, 'phone', None)
                }
                
                # Send critical lab result notification
                result = notification_manager.send_critical_lab_result(
                    patient_data=patient_data,
                    lab_data=lab_data,
                    physician_data=physician_data
                )
                
                import logging
                logger = logging.getLogger(__name__)
                if result.get('success'):
                    logger.critical(
                        f"✅ Critical lab result notification sent for patient {patient.patient_id}, "
                        f"report {instance.report_id} to Dr. {physician.user.get_full_name()}"
                    )
                else:
                    logger.error(
                        f"❌ Failed to send critical lab result notification for patient {patient.patient_id}, "
                        f"report {instance.report_id}: {result.get('error', 'Unknown error')}"
                    )
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"❌ No ordering physician found for critical result: Report {instance.report_id} "
                    f"for patient {patient.full_name}"
                )
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Critical result notification failed: {e}")
            logger.warning(
                f"Manual follow-up required: Critical pathology result {instance.report_id} "
                f"for patient {instance.order_test.order.patient.full_name}"
            )
