from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid
import json

User = get_user_model()

class S3UploadedFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    file_key = models.CharField(max_length=1024, unique=True)
    bucket_name = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    upload_time = models.DateTimeField(auto_now_add=True)
    file_url = models.URLField(max_length=2048, blank=True)

    def __str__(self):
        return self.original_filename


class S3LibraryBook(models.Model):
    """
    Model to track books in the S3 library for quick access and metadata.
    """
    CATEGORY_CHOICES = [
        ('medical_books', 'Medical Books'),
        ('nursing_books', 'Nursing Books'),
        ('research_papers', 'Research Papers'),
        ('study_notes', 'Study Notes'),
        ('reference_materials', 'Reference Materials'),
        ('exam_prep', 'Exam Preparation'),
        ('clinical_guidelines', 'Clinical Guidelines'),
        ('medical_journals', 'Medical Journals'),
    ]
    
    title = models.CharField(max_length=500)
    s3_key = models.CharField(max_length=1024, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Size in bytes
    content_type = models.CharField(max_length=100)
    
    # Metadata
    author = models.CharField(max_length=300, blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    publication_year = models.IntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, null=True, help_text="Comma-separated tags")
    
    # Tracking
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    # MCQ Generation tracking
    mcq_generation_count = models.IntegerField(default=0)
    last_mcq_generated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['tags']),
            models.Index(fields=['-last_accessed']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.category})"
    
    @property
    def size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def tag_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


class MCQGenerationHistory(models.Model):
    """
    Track MCQ generation history from S3 library books.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    library_book = models.ForeignKey(S3LibraryBook, on_delete=models.CASCADE, null=True, blank=True)
    s3_key = models.CharField(max_length=1024)  # For books not in library model
    filename = models.CharField(max_length=255)
    
    # Generation parameters
    num_questions = models.IntegerField()
    generation_type = models.CharField(max_length=20, choices=[
        ('full_book_wise', 'Full Book'),
        ('chapter_wise', 'Chapter Wise')
    ])
    
    # Results
    questions_generated = models.IntegerField(default=0)
    generation_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)

# ============================================================================
# SECURE S3 DATA MANAGEMENT MODELS
# HIPAA-Compliant database models for tracking S3 operations
# ============================================================================

class UserWorkspace(models.Model):
    """Track user workspaces in S3"""
    
    WORKSPACE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='s3_workspaces')
    module = models.CharField(max_length=50, choices=[
        ('radiology', 'Radiology'),
        ('medicine', 'Medicine'),
        ('dentistry', 'Dentistry'),
        ('dermatology', 'Dermatology'),
        ('pathology', 'Pathology'),
        ('homeopathy', 'Homeopathy'),
        ('allopathy', 'Allopathy'),
        ('cosmetology', 'Cosmetology'),
        ('dna_sequencing', 'DNA Sequencing'),
        ('secureneat', 'SecureNeat'),
        ('netflix', 'Netflix')
    ])
    s3_path = models.CharField(max_length=500, help_text="Base S3 path for user workspace")
    status = models.CharField(max_length=20, choices=WORKSPACE_STATUS_CHOICES, default='active')
    storage_quota_gb = models.IntegerField(default=10, help_text="Storage quota in GB")
    current_usage_bytes = models.BigIntegerField(default=0, help_text="Current storage usage in bytes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'module']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.module} workspace"
    
    @property
    def usage_percentage(self):
        """Calculate storage usage percentage"""
        if self.storage_quota_gb == 0:
            return 0
        quota_bytes = self.storage_quota_gb * 1024 * 1024 * 1024
        return (self.current_usage_bytes / quota_bytes) * 100
    
    @property
    def remaining_space_gb(self):
        """Calculate remaining space in GB"""
        quota_bytes = self.storage_quota_gb * 1024 * 1024 * 1024
        remaining_bytes = quota_bytes - self.current_usage_bytes
        return max(0, remaining_bytes / (1024 * 1024 * 1024))

class PatientFolder(models.Model):
    """Track patient folders created by doctors/admins"""
    
    FOLDER_STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('transferred', 'Transferred'),
        ('deleted', 'Deleted')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.CharField(max_length=100, help_text="Patient identifier")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_patient_folders')
    assigned_doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_patient_folders')
    module = models.CharField(max_length=50, choices=[
        ('radiology', 'Radiology'),
        ('medicine', 'Medicine'),
        ('dentistry', 'Dentistry'),
        ('dermatology', 'Dermatology'),
        ('pathology', 'Pathology'),
        ('homeopathy', 'Homeopathy'),
        ('allopathy', 'Allopathy'),
        ('cosmetology', 'Cosmetology')
    ])
    s3_path = models.CharField(max_length=500, help_text="S3 path to patient folder")
    status = models.CharField(max_length=20, choices=FOLDER_STATUS_CHOICES, default='active')
    
    # Patient metadata (encrypted in S3)
    encrypted_metadata_key = models.CharField(max_length=200, help_text="S3 key for encrypted patient metadata")
    
    # Access control
    access_permissions = models.JSONField(default=dict, help_text="JSON field for access permissions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient_id', 'module', 'assigned_doctor']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Patient {self.patient_id} - {self.module} ({self.assigned_doctor})"

class S3FileRecord(models.Model):
    """Track individual files in S3 for audit and management"""
    
    FILE_STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
        ('quarantined', 'Quarantined')
    ]
    
    FILE_TYPE_CHOICES = [
        ('medical_record', 'Medical Record'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Medical Imaging'),
        ('prescription', 'Prescription'),
        ('treatment_plan', 'Treatment Plan'),
        ('progress_note', 'Progress Note'),
        ('discharge_summary', 'Discharge Summary'),
        ('consent_form', 'Consent Form'),
        ('report', 'Report'),
        ('document', 'General Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_folder = models.ForeignKey(PatientFolder, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # File information
    original_filename = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500, unique=True, help_text="Full S3 key/path")
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES)
    content_type = models.CharField(max_length=100)
    file_size_bytes = models.BigIntegerField()
    checksum = models.CharField(max_length=64, help_text="SHA256 checksum")
    
    # Security
    is_encrypted = models.BooleanField(default=True)
    encryption_algorithm = models.CharField(max_length=50, default='Fernet')
    access_level = models.CharField(max_length=30, default='hipaa_protected')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=FILE_STATUS_CHOICES, default='uploaded')
    metadata = models.JSONField(default=dict, help_text="Additional file metadata")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.original_filename} ({self.patient_folder.patient_id})"
    
    @property
    def file_size_mb(self):
        """File size in MB"""
        return round(self.file_size_bytes / (1024 * 1024), 2)

class S3AuditLog(models.Model):
    """Comprehensive audit log for S3 operations"""
    
    ACTION_CHOICES = [
        ('workspace_created', 'Workspace Created'),
        ('patient_folder_created', 'Patient Folder Created'),
        ('file_uploaded', 'File Uploaded'),
        ('file_accessed', 'File Accessed'),
        ('file_downloaded', 'File Downloaded'),
        ('file_deleted', 'File Deleted'),
        ('file_moved', 'File Moved'),
        ('permission_granted', 'Permission Granted'),
        ('permission_revoked', 'Permission Revoked'),
        ('folder_accessed', 'Folder Accessed'),
        ('metadata_updated', 'Metadata Updated'),
        ('backup_created', 'Backup Created'),
        ('system_maintenance', 'System Maintenance')
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    
    # Target information
    patient_id = models.CharField(max_length=100, null=True, blank=True)
    s3_key = models.CharField(max_length=500, null=True, blank=True)
    
    # Audit details
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Action details
    action_details = models.JSONField(default=dict)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    
    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['patient_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
        ]
        
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

class AccessPermission(models.Model):
    """Fine-grained access permissions for S3 resources"""
    
    PERMISSION_TYPE_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('delete', 'Delete'),
        ('admin', 'Admin')
    ]
    
    RESOURCE_TYPE_CHOICES = [
        ('workspace', 'Workspace'),
        ('patient_folder', 'Patient Folder'),
        ('file', 'File'),
        ('module', 'Module')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='s3_permissions')
    
    # Permission details
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPE_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    resource_id = models.CharField(max_length=100, help_text="ID of the resource (workspace, folder, file)")
    module = models.CharField(max_length=50)
    
    # Access control
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Leave blank for permanent access")
    
    # Conditions
    ip_restrictions = models.JSONField(default=list, help_text="List of allowed IP addresses/ranges")
    time_restrictions = models.JSONField(default=dict, help_text="Time-based access restrictions")
    
    # Status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='revoked_permissions')
    
    class Meta:
        unique_together = ['user', 'permission_type', 'resource_type', 'resource_id']
        ordering = ['-granted_at']
        
    def __str__(self):
        return f"{self.user} - {self.permission_type} on {self.resource_type} {self.resource_id}"
    
    @property
    def is_expired(self):
        """Check if permission has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False