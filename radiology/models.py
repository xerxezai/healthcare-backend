from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
import uuid

class Institution(models.Model):
    """Institution/Hospital information - minimal data in PostgreSQL."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # Hospital code
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # S3 configuration for this institution
    s3_prefix = models.CharField(max_length=100, unique=True)  # radiology/institutions/{uuid}/
    storage_quota_gb = models.IntegerField(default=1000)  # Storage quota in GB
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']

class RadiologyPatient(models.Model):
    """Patient information - only reference data in PostgreSQL, details in S3."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='patients')
    
    # Basic identifiers (non-sensitive)
    patient_code = models.CharField(max_length=50)  # Hospital patient ID
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # S3 reference
    s3_patient_prefix = models.CharField(max_length=200)  # Full S3 path to patient data
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Search optimization fields (duplicated from S3 for query performance)
    last_study_date = models.DateTimeField(null=True, blank=True)
    total_studies = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_code})"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['institution', 'patient_code']

class RadiologyStudy(models.Model):
    """Study information - minimal data in PostgreSQL, details in S3."""
    MODALITY_CHOICES = [
        ('CT', 'Computed Tomography'),
        ('MRI', 'Magnetic Resonance Imaging'),
        ('XR', 'X-Ray'),
        ('US', 'Ultrasound'),
        ('NM', 'Nuclear Medicine'),
        ('PET', 'Positron Emission Tomography'),
        ('MG', 'Mammography'),
        ('CR', 'Computed Radiography'),
        ('DR', 'Digital Radiography'),
        ('FL', 'Fluoroscopy'),
        ('DX', 'Digital X-Ray'),
        ('OTHER', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reported', 'Reported'),
        ('finalized', 'Finalized'),
        ('cancelled', 'Cancelled')
    ]
    
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
        ('stat', 'STAT')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(RadiologyPatient, on_delete=models.CASCADE, related_name='studies')
    
    # Study identifiers
    accession_number = models.CharField(max_length=50, unique=True)
    study_instance_uid = models.CharField(max_length=100, unique=True, blank=True)
    
    # Basic study info
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES)
    body_part = models.CharField(max_length=100)
    study_description = models.TextField()
    clinical_indication = models.TextField(blank=True)
    
    # Scheduling info
    study_date = models.DateTimeField()
    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='ordered_studies'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='performed_studies'
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    
    # S3 reference
    s3_study_prefix = models.CharField(max_length=300)  # Full S3 path to study data
    
    # File tracking (for quick queries)
    dicom_file_count = models.IntegerField(default=0)
    total_file_size_mb = models.FloatField(default=0.0)
    has_report = models.BooleanField(default=False)
    has_ai_analysis = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.accession_number} - {self.modality} {self.body_part}"
    
    class Meta:
        ordering = ['-study_date']

class RadiologyReport(models.Model):
    """Report metadata - content stored in S3."""
    REPORT_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('preliminary', 'Preliminary'),
        ('final', 'Final'),
        ('amended', 'Amended'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.ForeignKey(RadiologyStudy, on_delete=models.CASCADE, related_name='reports')
    
    # Report metadata
    report_type = models.CharField(max_length=50, default='radiology')
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='draft')
    version = models.CharField(max_length=10, default='1.0')
    
    # Creator info
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='signed_reports'
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # AI assistance tracking
    ai_assisted = models.BooleanField(default=False)
    ai_model_version = models.CharField(max_length=50, blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    
    # S3 reference
    s3_report_key = models.CharField(max_length=400)  # Full S3 key to report content
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Report for {self.study.accession_number} v{self.version}"
    
    class Meta:
        ordering = ['-created_at']

class AIAnalysisResult(models.Model):
    """AI analysis result metadata - content stored in S3."""
    ANALYSIS_TYPE_CHOICES = [
        ('rads_calculator', 'RADS Calculator'),
        ('report_correction', 'Report Correction'),
        ('image_analysis', 'Image Analysis'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('measurement', 'Automated Measurement'),
        ('classification', 'Image Classification'),
        ('segmentation', 'Image Segmentation'),
        ('other', 'Other Analysis')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.ForeignKey(RadiologyStudy, on_delete=models.CASCADE, related_name='ai_analyses')
    
    # Analysis metadata
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES)
    ai_model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    
    # Results summary
    confidence_score = models.FloatField(null=True, blank=True)
    processing_time_seconds = models.FloatField(null=True, blank=True)
    has_flags = models.BooleanField(default=False)  # Critical findings flag
    
    # Creator info
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # S3 reference
    s3_analysis_key = models.CharField(max_length=400)  # Full S3 key to analysis results
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} for {self.study.accession_number}"
    
    class Meta:
        ordering = ['-created_at']

class DoctorWorkspace(models.Model):
    """Doctor workspace metadata - content stored in S3."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    # Specialization info
    specializations = models.JSONField(default=list)  # ["Cardiology", "Interventional"]
    
    # S3 reference
    s3_workspace_prefix = models.CharField(max_length=300)  # Full S3 path to workspace
    
    # Usage statistics
    total_reports_created = models.IntegerField(default=0)
    total_ai_analyses = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Workspace for Dr. {self.doctor.get_full_name()}"
    
    class Meta:
        unique_together = ['doctor', 'institution']

class ProcessedDocument(models.Model):
    """Legacy model - keeping for backward compatibility."""
    ANALYSIS_TYPE_CHOICES = [
        ('anonymization', 'Anonymization'),
        ('report_analysis', 'Report Analysis'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='processed_documents')
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    processing_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # For anonymization
    redacted_item_counts = models.JSONField(null=True, blank=True, help_text="e.g., {'Patient Names': 2, 'Dates': 1}")
    
    # For report analysis
    accuracy_score = models.FloatField(null=True, blank=True)
    error_distribution = models.JSONField(null=True, blank=True, help_text="e.g., {'Medical Errors': 1, 'Typos': 2}")
    
    # Input/Output (could be S3 keys or snippets)
    input_preview = models.TextField(blank=True, null=True, help_text="Snippet of input text")
    output_preview = models.TextField(blank=True, null=True, help_text="Snippet of output/anonymized text or summary of analysis")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_processing_type_display()} of {self.original_filename or 'text input'} for {self.user.email}"

    class Meta:
        ordering = ['-created_at']

class AuditLog(models.Model):
    """Audit log for data access and modifications."""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('download', 'Download'),
        ('upload', 'Upload')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who performed the action
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    # What was accessed
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # 'patient', 'study', 'report', etc.
    resource_id = models.UUIDField()  # ID of the accessed resource
    
    # Additional details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)  # Additional context
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.resource_type} at {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['institution', 'created_at']),
        ]