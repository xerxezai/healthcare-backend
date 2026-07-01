# Signal handlers for Netflix app
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import (
    ContentAuditLog, UserEntitlements, EnhancedRole, 
    UserRoleAssignment, Title, Episode, Asset, ManualPayment
)

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_entitlements(sender, instance, created, **kwargs):
    """Create default entitlements for new users"""
    if created:
        UserEntitlements.objects.get_or_create(
            user=instance,
            defaults={
                'account_status': 'TRIAL',
                'stream_access': True,
                'max_profiles': 1,
                'max_devices': 2,
                'hd_enabled': False,
                'uhd_enabled': False,
                'region_access': ['US'],  # Default region
            }
        )


@receiver(post_save, sender=Title)
def log_title_changes(sender, instance, created, **kwargs):
    """Log title creation/updates"""
    action = 'CREATE' if created else 'UPDATE'
    ContentAuditLog.objects.create(
        actor_user=getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None),
        action=action,
        entity_type='title',
        entity_id=str(instance.id),
        entity_name=instance.name,
        new_values={
            'name': instance.name,
            'type': instance.type,
            'visibility': instance.visibility,
        }
    )


@receiver(post_save, sender=Episode)
def log_episode_changes(sender, instance, created, **kwargs):
    """Log episode creation/updates"""
    action = 'CREATE' if created else 'UPDATE'
    ContentAuditLog.objects.create(
        action=action,
        entity_type='episode',
        entity_id=str(instance.id),
        entity_name=f"{instance.season.title.name} S{instance.season.number}E{instance.number}: {instance.name}",
        new_values={
            'name': instance.name,
            'season': instance.season.number,
            'episode': instance.number,
        }
    )


@receiver(post_save, sender=Asset)
def log_asset_changes(sender, instance, created, **kwargs):
    """Log asset uploads/changes"""
    action = 'UPLOAD' if created else 'UPDATE'
    ContentAuditLog.objects.create(
        action=action,
        entity_type='asset',
        entity_id=str(instance.id),
        entity_name=f"{instance.kind} - {instance.file_name}",
        new_values={
            'kind': instance.kind,
            'file_name': instance.file_name,
            'quality': instance.quality,
        }
    )


@receiver(post_save, sender=ManualPayment)
def log_payment_recording(sender, instance, created, **kwargs):
    """Log manual payment recordings"""
    if created:
        ContentAuditLog.objects.create(
            actor_user=instance.recorded_by,
            action='PAYMENT',
            entity_type='payment',
            entity_id=str(instance.id),
            entity_name=f"{instance.amount} {instance.currency} - {instance.method}",
            new_values={
                'user': instance.user.email,
                'amount': str(instance.amount),
                'currency': instance.currency,
                'method': instance.method,
                'reference_no': instance.reference_no,
            }
        )


@receiver(post_save, sender=UserEntitlements)
def log_entitlement_changes(sender, instance, created, **kwargs):
    """Log entitlement modifications"""
    if not created:  # Only log updates, not creation
        ContentAuditLog.objects.create(
            actor_user=instance.last_modified_by,
            action='ENTITLEMENT_CHANGE',
            entity_type='entitlement',
            entity_id=str(instance.user.id),
            entity_name=instance.user.email,
            new_values={
                'account_status': instance.account_status,
                'stream_access': instance.stream_access,
                'max_profiles': instance.max_profiles,
                'max_devices': instance.max_devices,
                'hd_enabled': instance.hd_enabled,
                'uhd_enabled': instance.uhd_enabled,
                'reason': instance.modification_reason,
            }
        )


@receiver(post_delete, sender=Title)
def log_title_deletion(sender, instance, **kwargs):
    """Log title deletions"""
    ContentAuditLog.objects.create(
        action='DELETE',
        entity_type='title',
        entity_id=str(instance.id),
        entity_name=instance.name,
        old_values={
            'name': instance.name,
            'type': instance.type,
            'visibility': instance.visibility,
        }
    )
