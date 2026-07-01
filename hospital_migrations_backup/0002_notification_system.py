# Django Database Migration for Notification System
# Generated for Healthcare Platform

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0001_initial'),  # Adjust based on your latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[
                    ('registration_confirmation', 'Registration Confirmation'),
                    ('admin_approval_required', 'Admin Approval Required'),
                    ('account_approved', 'Account Approved'),
                    ('password_reset', 'Password Reset'),
                    ('appointment_reminder_email', 'Appointment Reminder Email'),
                    ('appointment_reminder_sms', 'Appointment Reminder SMS'),
                    ('credential_expiry_warning', 'Credential Expiry Warning'),
                    ('compliance_notification', 'Compliance Notification'),
                    ('system_alert', 'System Alert'),
                ], max_length=50)),
                ('recipient', models.CharField(max_length=255)),
                ('success', models.BooleanField(default=False)),
                ('service_used', models.CharField(choices=[
                    ('ses', 'AWS SES'),
                    ('sns', 'AWS SNS'),
                    ('django_smtp', 'Django SMTP'),
                    ('unknown', 'Unknown'),
                ], default='unknown', max_length=20)),
                ('message_id', models.CharField(blank=True, max_length=255)),
                ('error_message', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification_logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_type', models.CharField(max_length=50, unique=True)),
                ('subject_template', models.CharField(max_length=255)),
                ('email_template', models.TextField()),
                ('sms_template', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'notification_templates',
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_appointment_reminders', models.BooleanField(default=True)),
                ('sms_appointment_reminders', models.BooleanField(default=True)),
                ('email_system_alerts', models.BooleanField(default=True)),
                ('email_compliance_notifications', models.BooleanField(default=True)),
                ('email_credential_warnings', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification_preferences',
            },
        ),
        migrations.CreateModel(
            name='ScheduledNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(max_length=50)),
                ('recipient_email', models.EmailField(blank=True, max_length=254)),
                ('recipient_phone', models.CharField(blank=True, max_length=20)),
                ('subject', models.CharField(max_length=255)),
                ('message_data', models.JSONField()),
                ('scheduled_time', models.DateTimeField()),
                ('priority', models.CharField(choices=[
                    ('low', 'Low'),
                    ('normal', 'Normal'),
                    ('high', 'High'),
                    ('critical', 'Critical'),
                ], default='normal', max_length=10)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                    ('cancelled', 'Cancelled'),
                ], default='pending', max_length=10)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('max_attempts', models.PositiveIntegerField(default=3)),
                ('last_attempt', models.DateTimeField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'scheduled_notifications',
                'ordering': ['scheduled_time', 'priority'],
            },
        ),
        # Add indexes for better performance
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['notification_type'], name='notif_logs_type_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['recipient'], name='notif_logs_recipient_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['success'], name='notif_logs_success_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['timestamp'], name='notif_logs_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednotification',
            index=models.Index(fields=['status'], name='sched_notif_status_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednotification',
            index=models.Index(fields=['scheduled_time'], name='sched_notif_time_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednotification',
            index=models.Index(fields=['priority'], name='sched_notif_priority_idx'),
        ),
    ]
