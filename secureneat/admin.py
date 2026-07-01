from django.contrib import admin
from .models import (
    S3UploadedFile, S3LibraryBook, MCQGenerationHistory,
    UserWorkspace, PatientFolder, S3FileRecord, S3AuditLog, AccessPermission
)
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json


@admin.register(S3UploadedFile)
class S3UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'file_key', 'user', 'upload_time', 'content_type')
    list_filter = ('content_type', 'upload_time')
    search_fields = ('original_filename', 'file_key', 'user__email')


@admin.register(S3LibraryBook)
class S3LibraryBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subcategory', 'author', 'size_mb', 'access_count', 'mcq_generation_count', 'date_added']
    list_filter = ['category', 'subcategory', 'date_added', 'publication_year']
    search_fields = ['title', 'author', 'tags', 'description']
    readonly_fields = ['s3_key', 'file_size', 'date_added', 'last_accessed', 'access_count', 'mcq_generation_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'subcategory', 'filename', 'content_type')
        }),
        ('Metadata', {
            'fields': ('author', 'publisher', 'publication_year', 'isbn', 'description', 'tags')
        }),
        ('Technical Details', {
            'fields': ('s3_key', 'file_size', 'added_by'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('date_added', 'last_accessed', 'access_count', 'mcq_generation_count', 'last_mcq_generated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MCQGenerationHistory)
class MCQGenerationHistoryAdmin(admin.ModelAdmin):
    list_display = ['filename', 'user', 'num_questions', 'generation_type', 'questions_generated', 'generation_successful', 'created_at']
    list_filter = ['generation_type', 'generation_successful', 'created_at']
    search_fields = ['filename', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'library_book', 's3_key', 'filename')
        }),
        ('Generation Parameters', {
            'fields': ('num_questions', 'generation_type')
        }),
        ('Results', {
            'fields': ('questions_generated', 'generation_successful', 'error_message')
        }),
        ('Timing', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# ============================================================================
# SECURE S3 DATA MANAGEMENT ADMIN
# HIPAA-Compliant administration interface
# ============================================================================

@admin.register(UserWorkspace)
class UserWorkspaceAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'module', 'status', 'usage_percentage_display', 'patient_folders_count', 'created_at']
    list_filter = ['module', 'status', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'module']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_accessed', 'usage_percentage', 'remaining_space_gb']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def usage_percentage_display(self, obj):
        percentage = obj.usage_percentage
        if percentage < 50:
            color = 'green'
        elif percentage < 80:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            percentage
        )
    usage_percentage_display.short_description = 'Usage %'
    
    def patient_folders_count(self, obj):
        return PatientFolder.objects.filter(
            assigned_doctor=obj.user,
            module=obj.module,
            status='active'
        ).count()
    patient_folders_count.short_description = 'Patient Folders'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'module', 'status')
        }),
        ('Storage Information', {
            'fields': ('s3_path', 'storage_quota_gb', 'current_usage_bytes', 'usage_percentage', 'remaining_space_gb')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PatientFolder)
class PatientFolderAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'assigned_doctor_name', 'module', 'status', 'files_count', 'total_size_mb', 'created_at']
    list_filter = ['module', 'status', 'created_at', 'assigned_doctor']
    search_fields = ['patient_id', 'assigned_doctor__email', 'assigned_doctor__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_accessed', 'files_count', 'total_size_mb']
    
    def assigned_doctor_name(self, obj):
        if obj.assigned_doctor:
            return f"{obj.assigned_doctor.full_name} ({obj.assigned_doctor.email})"
        return "No assigned doctor"
    assigned_doctor_name.short_description = 'Assigned Doctor'
    
    def files_count(self, obj):
        return obj.files.filter(status='uploaded').count()
    files_count.short_description = 'Files Count'
    
    def total_size_mb(self, obj):
        total_bytes = sum(f.file_size_bytes for f in obj.files.filter(status='uploaded'))
        return f"{total_bytes / (1024 * 1024):.2f} MB"
    total_size_mb.short_description = 'Total Size'
    
    def access_permissions_display(self, obj):
        if obj.access_permissions:
            return format_html('<pre>{}</pre>', json.dumps(obj.access_permissions, indent=2))
        return "No permissions set"
    access_permissions_display.short_description = 'Access Permissions'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'assigned_doctor', 'created_by', 'module')
        }),
        ('Storage Information', {
            'fields': ('s3_path', 'status', 'encrypted_metadata_key')
        }),
        ('Access Control', {
            'fields': ('access_permissions_display',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('files_count', 'total_size_mb'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )

@admin.register(S3FileRecord)
class S3FileRecordAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'patient_id_display', 'file_type', 'status', 'file_size_mb_display', 'uploaded_by_name', 'uploaded_at']
    list_filter = ['file_type', 'status', 'is_encrypted', 'content_type', 'uploaded_at']
    search_fields = ['original_filename', 'patient_folder__patient_id', 'uploaded_by__email']
    readonly_fields = ['id', 'checksum', 'uploaded_at', 'last_accessed', 'file_size_mb']
    
    def patient_id_display(self, obj):
        return obj.patient_folder.patient_id
    patient_id_display.short_description = 'Patient ID'
    
    def uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.full_name} ({obj.uploaded_by.role})"
        return "Unknown"
    uploaded_by_name.short_description = 'Uploaded By'
    
    def file_size_mb_display(self, obj):
        return f"{obj.file_size_mb} MB"
    file_size_mb_display.short_description = 'Size'
    
    def metadata_display(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return "No metadata"
    metadata_display.short_description = 'Metadata'
    
    fieldsets = (
        ('File Information', {
            'fields': ('original_filename', 'patient_folder', 'uploaded_by', 'file_type')
        }),
        ('Storage Information', {
            'fields': ('s3_key', 'content_type', 'file_size_bytes', 'file_size_mb', 'checksum')
        }),
        ('Security', {
            'fields': ('is_encrypted', 'encryption_algorithm', 'access_level', 'status')
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'last_accessed', 'archived_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(S3AuditLog)
class S3AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'action', 'module', 'patient_id', 'risk_level', 'success', 'timestamp']
    list_filter = ['action', 'module', 'risk_level', 'success', 'timestamp']
    search_fields = ['user__email', 'patient_id', 's3_key', 'action']
    readonly_fields = ['id', 'timestamp', 'action_details_display']
    date_hierarchy = 'timestamp'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.full_name} ({obj.user.role})"
        return "System"
    user_display.short_description = 'User'
    
    def action_details_display(self, obj):
        if obj.action_details:
            return format_html('<pre>{}</pre>', json.dumps(obj.action_details, indent=2))
        return "No details"
    action_details_display.short_description = 'Action Details'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Super admin can see all logs
        if request.user.role == 'super_admin':
            return qs
        # Admin can see logs for their modules
        elif request.user.role == 'admin':
            # This would filter based on admin's module access
            return qs  # Simplified for now
        else:
            # Regular users can only see their own actions
            return qs.filter(user=request.user)
    
    fieldsets = (
        ('Action Information', {
            'fields': ('user', 'action', 'module', 'success')
        }),
        ('Target Information', {
            'fields': ('patient_id', 's3_key', 'risk_level')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('action_details_display', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'permission_type', 'resource_type', 'resource_id', 'module', 'is_active', 'expires_at']
    list_filter = ['permission_type', 'resource_type', 'module', 'is_active', 'granted_at']
    search_fields = ['user__email', 'resource_id', 'module']
    readonly_fields = ['id', 'granted_at', 'revoked_at', 'is_expired']
    
    def user_display(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def ip_restrictions_display(self, obj):
        if obj.ip_restrictions:
            return format_html('<pre>{}</pre>', json.dumps(obj.ip_restrictions, indent=2))
        return "No IP restrictions"
    ip_restrictions_display.short_description = 'IP Restrictions'
    
    def time_restrictions_display(self, obj):
        if obj.time_restrictions:
            return format_html('<pre>{}</pre>', json.dumps(obj.time_restrictions, indent=2))
        return "No time restrictions"
    time_restrictions_display.short_description = 'Time Restrictions'
    
    fieldsets = (
        ('Permission Information', {
            'fields': ('user', 'permission_type', 'resource_type', 'resource_id', 'module')
        }),
        ('Grant Information', {
            'fields': ('granted_by', 'granted_at', 'expires_at', 'is_active')
        }),
        ('Restrictions', {
            'fields': ('ip_restrictions_display', 'time_restrictions_display'),
            'classes': ('collapse',)
        }),
        ('Revocation', {
            'fields': ('revoked_at', 'revoked_by'),
            'classes': ('collapse',)
        }),
    )