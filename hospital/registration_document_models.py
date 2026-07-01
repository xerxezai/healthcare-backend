"""
Registration Document Management System with Soft Coding
Handles file uploads for medical registration documents with AWS S3 integration
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import os

class RegistrationDocumentType(models.Model):
    """
    Soft-coded document types for registration
    Allows easy customization of required documents without code changes
    """
    # Configuration object for easy customization
    DOCUMENT_TYPE_CONFIG = {
        'validation': {
            'max_file_size_mb': 10,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'],
            'required_documents_count': 3
        },
        'categories': {
            'identity': 'Identity Verification',
            'license': 'Medical License',
            'education': 'Educational Credentials',
            'certification': 'Professional Certifications',
            'experience': 'Work Experience',
            'insurance': 'Professional Insurance'
        },
        'priority_levels': {
            'critical': 'Critical - Required for all registrations',
            'high': 'High - Required for specialists',
            'medium': 'Medium - Required for senior positions',
            'low': 'Low - Optional but recommended'
        }
    }
    
    name = models.CharField(max_length=100, help_text="Document type name")
    description = models.TextField(help_text="Description of what this document should contain")
    category = models.CharField(max_length=50, help_text="Document category for organization")
    is_required = models.BooleanField(default=True, help_text="Whether this document is mandatory")
    priority_level = models.CharField(max_length=20, default='medium', help_text="Priority level for review")
    file_size_limit_mb = models.IntegerField(default=10, help_text="Maximum file size in MB")
    allowed_extensions = models.JSONField(default=list, help_text="Allowed file extensions")
    display_order = models.IntegerField(default=0, help_text="Order for display in forms")
    is_active = models.BooleanField(default=True, help_text="Whether this document type is currently used")
    
    # Soft-coded validation rules
    validation_rules = models.JSONField(default=dict, help_text="Custom validation rules in JSON format")
    help_text = models.TextField(blank=True, help_text="Help text to show users")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Registration Document Type"
        verbose_name_plural = "Registration Document Types"
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    @classmethod
    def get_required_documents(cls, role='doctor'):
        """Get list of required documents for a specific role"""
        return cls.objects.filter(is_required=True, is_active=True).order_by('display_order')
    
    @classmethod
    def get_soft_config(cls):
        """Get soft-coded configuration for easy customization"""
        return cls.DOCUMENT_TYPE_CONFIG

def registration_document_upload_path(instance, filename):
    """
    Generate upload path for registration documents with soft-coded structure
    """
    # Soft-coded path configuration
    PATH_CONFIG = {
        'base_path': 'registration-documents',
        'organization_structure': 'user-id/document-type/timestamp',
        'filename_format': 'uuid_original-name',
        'max_path_length': 255
    }
    
    # Extract file extension
    ext = os.path.splitext(filename)[1]
    
    # Generate UUID for security
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # Create organized path structure
    return f"{PATH_CONFIG['base_path']}/{instance.user.id}/{instance.document_type.category}/{timezone.now().year}/{timezone.now().month:02d}/{unique_filename}"

class RegistrationDocument(models.Model):
    """
    Individual document uploads for registration with comprehensive tracking
    """
    # Configuration object for soft coding
    DOCUMENT_CONFIG = {
        'status_workflow': {
            'uploaded': 'Recently uploaded, pending review',
            'under_review': 'Being reviewed by administrators',
            'approved': 'Document verified and approved',
            'rejected': 'Document rejected, needs resubmission',
            'expired': 'Document has expired and needs renewal'
        },
        'security_settings': {
            'virus_scan_required': True,
            'encryption_required': True,
            'access_log_required': True,
            'retention_days': 2555  # 7 years for medical documents
        },
        'quality_checks': {
            'min_resolution': '300dpi',
            'max_file_size_mb': 10,
            'require_readable_text': True,
            'check_document_completeness': True
        }
    }
    
    DOCUMENT_STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registration_documents')
    document_type = models.ForeignKey(RegistrationDocumentType, on_delete=models.CASCADE)
    
    # File storage with S3 integration
    file = models.FileField(upload_to=registration_document_upload_path, help_text="Uploaded document file")
    original_filename = models.CharField(max_length=255, help_text="Original filename as uploaded by user")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, help_text="MIME type of the uploaded file")
    
    # Document status and validation
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='uploaded')
    validation_status = models.JSONField(default=dict, help_text="Detailed validation results")
    
    # Review and approval tracking
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Administrator notes about the document")
    
    # Security and tracking
    upload_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of uploader")
    access_count = models.IntegerField(default=0, help_text="Number of times document was accessed")
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Metadata for soft-coded features
    metadata = models.JSONField(default=dict, help_text="Additional document metadata")
    expiry_date = models.DateField(null=True, blank=True, help_text="Document expiry date (for licenses etc.)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Registration Document"
        verbose_name_plural = "Registration Documents"
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.document_type.name} ({self.status})"
    
    def get_file_url(self):
        """Get secure URL for file access"""
        if self.file:
            return self.file.url
        return None
    
    def mark_accessed(self, by_user=None):
        """Track document access for security auditing"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])
        
        # Log access for security
        RegistrationDocumentAccess.objects.create(
            document=self,
            accessed_by=by_user,
            access_type='view'
        )
    
    def is_expired(self):
        """Check if document has expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def get_validation_summary(self):
        """Get human-readable validation summary"""
        if not self.validation_status:
            return "Pending validation"
        
        issues = self.validation_status.get('issues', [])
        if not issues:
            return "✅ All validations passed"
        
        return f"⚠️ {len(issues)} validation issues found"
    
    @classmethod
    def get_soft_config(cls):
        """Get soft-coded configuration"""
        return cls.DOCUMENT_CONFIG

class RegistrationDocumentAccess(models.Model):
    """
    Audit trail for document access (security requirement for medical documents)
    """
    ACCESS_TYPE_CHOICES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('admin_review', 'Admin Review'),
    ]
    
    document = models.ForeignKey(RegistrationDocument, on_delete=models.CASCADE, related_name='access_logs')
    accessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPE_CHOICES)
    access_ip = models.GenericIPAddressField(help_text="IP address of accessor")
    user_agent = models.TextField(help_text="Browser/client information")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Document Access Log"
        verbose_name_plural = "Document Access Logs"

class RegistrationDocumentTemplate(models.Model):
    """
    Soft-coded templates for document requirements
    Allows easy customization of document requirements for different roles/regions
    """
    TEMPLATE_CONFIG = {
        'roles': {
            'general_doctor': 'General Medical Practitioner',
            'specialist': 'Medical Specialist',
            'nurse_practitioner': 'Nurse Practitioner',
            'physician_assistant': 'Physician Assistant'
        },
        'regions': {
            'us': 'United States',
            'eu': 'European Union',
            'uk': 'United Kingdom',
            'india': 'India',
            'canada': 'Canada'
        },
        'template_versions': {
            '1.0': 'Basic requirements',
            '2.0': 'Enhanced security requirements',
            '2.1': 'GDPR compliance added'
        }
    }
    
    name = models.CharField(max_length=100, help_text="Template name")
    description = models.TextField(help_text="Template description")
    role = models.CharField(max_length=50, help_text="Target role for this template")
    region = models.CharField(max_length=20, help_text="Geographic region")
    version = models.CharField(max_length=10, default='1.0', help_text="Template version")
    
    document_types = models.ManyToManyField(RegistrationDocumentType, help_text="Required document types")
    
    # Soft-coded requirements
    requirements = models.JSONField(default=dict, help_text="Detailed requirements in JSON format")
    validation_rules = models.JSONField(default=dict, help_text="Validation rules for this template")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name', '-version']
        unique_together = ['name', 'version']
        verbose_name = "Registration Document Template"
        verbose_name_plural = "Registration Document Templates"
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.role})"
    
    @classmethod
    def get_template_for_role(cls, role, region='general'):
        """Get appropriate document template for role and region"""
        return cls.objects.filter(
            role=role,
            region=region,
            is_active=True
        ).order_by('-version').first()
    
    @classmethod
    def get_soft_config(cls):
        """Get soft-coded configuration"""
        return cls.TEMPLATE_CONFIG
