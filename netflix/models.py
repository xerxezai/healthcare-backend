# Netflix-like Content Management System Models
# Designed to work alongside existing healthcare system

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Genre(models.Model):
    """Content genres/categories"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Title(models.Model):
    """Main content titles (movies, series, documentaries)"""
    TITLE_TYPES = [
        ('MOVIE', 'Movie'),
        ('SERIES', 'TV Series'),
        ('DOCUMENTARY', 'Documentary'),
        ('SHORT', 'Short Film'),
        ('EDUCATIONAL', 'Educational Content'),
    ]
    
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('RESTRICTED', 'Restricted'),
    ]
    
    RATING_CHOICES = [
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance'),
        ('PG13', 'Parents Strongly Cautioned'),
        ('R', 'Restricted'),
        ('NC17', 'Adults Only'),
        ('NR', 'Not Rated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=20, choices=TITLE_TYPES)
    name = models.CharField(max_length=200)
    synopsis = models.TextField()
    release_year = models.PositiveIntegerField()
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    genres = models.ManyToManyField(Genre, related_name='titles')
    tags = models.JSONField(default=list)  # Custom tags
    regions = models.JSONField(default=list)  # Available regions ['US', 'CA', 'UK']
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    
    # Metadata
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)  # For movies
    imdb_id = models.CharField(max_length=20, blank=True)
    tmdb_id = models.CharField(max_length=20, blank=True)
    
    # Management fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_titles')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_titles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'visibility']),
            models.Index(fields=['release_year']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.release_year})"


class Season(models.Model):
    """TV Series seasons"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name='seasons')
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=200, blank=True)
    overview = models.TextField(blank=True)
    air_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('title', 'number')
        ordering = ['number']
    
    def __str__(self):
        return f"{self.title.name} - Season {self.number}"


class Episode(models.Model):
    """Individual episodes within seasons"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    synopsis = models.TextField()
    runtime_minutes = models.PositiveIntegerField()
    air_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('season', 'number')
        ordering = ['number']
    
    def __str__(self):
        return f"{self.season.title.name} S{self.season.number}E{self.number}: {self.name}"


class Asset(models.Model):
    """Media assets for titles and episodes"""
    ASSET_KINDS = [
        ('VIDEO', 'Video File'),
        ('THUMBNAIL', 'Thumbnail Image'),
        ('SUBTITLE', 'Subtitle Track'),
        ('AUDIO', 'Audio Track'),
        ('POSTER', 'Poster Image'),
        ('BACKDROP', 'Backdrop Image'),
        ('TRAILER', 'Trailer Video'),
    ]
    
    QUALITY_CHOICES = [
        ('240p', '240p'),
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p (HD)'),
        ('1080p', '1080p (Full HD)'),
        ('1440p', '1440p (2K)'),
        ('2160p', '2160p (4K)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.ForeignKey(Title, on_delete=models.CASCADE, null=True, blank=True, related_name='assets')
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True, related_name='assets')
    
    kind = models.CharField(max_length=20, choices=ASSET_KINDS)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()  # S3 or CDN URL
    file_size = models.BigIntegerField(null=True, blank=True)  # bytes
    
    # Video/Audio specific
    codec = models.CharField(max_length=20, blank=True)  # H.264, H.265, AAC, etc.
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, blank=True)
    bitrate = models.PositiveIntegerField(null=True, blank=True)  # kbps
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Subtitle specific
    language = models.CharField(max_length=10, blank=True)  # en, es, fr, etc.
    
    # Security
    checksum = models.CharField(max_length=64, blank=True)
    drm_protected = models.BooleanField(default=False)
    encryption_key_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['kind', 'quality']),
            models.Index(fields=['language']),
        ]
    
    def __str__(self):
        target = self.episode or self.title
        return f"{target} - {self.kind} ({self.quality or 'N/A'})"


class UserProfile(models.Model):
    """User viewing profiles - extends existing user system"""
    MATURITY_RATINGS = [
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance'),
        ('PG13', 'Parents Strongly Cautioned'),
        ('R', 'Restricted'),
        ('NC17', 'Adults Only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewing_profiles')
    name = models.CharField(max_length=50)
    avatar_url = models.URLField(blank=True)
    maturity_rating = models.CharField(max_length=10, choices=MATURITY_RATINGS, default='R')
    pin = models.CharField(max_length=10, blank=True)  # Profile PIN
    is_kid = models.BooleanField(default=False)
    language_preference = models.CharField(max_length=10, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'name')
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class UserEntitlements(models.Model):
    """Manual account entitlements replacing subscription system"""
    ACCOUNT_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('LOCKED', 'Locked'),
        ('TRIAL', 'Trial'),
        ('EXPIRED', 'Expired'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='netflix_entitlements')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='TRIAL')
    
    # Manual Entitlements
    stream_access = models.BooleanField(default=True)
    max_profiles = models.PositiveIntegerField(default=1)
    max_devices = models.PositiveIntegerField(default=2)
    hd_enabled = models.BooleanField(default=False)
    uhd_enabled = models.BooleanField(default=False)
    download_enabled = models.BooleanField(default=False)
    region_access = models.JSONField(default=list)  # ['US', 'CA', 'UK']
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='entitlement_changes', on_delete=models.SET_NULL, null=True)
    modification_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.account_status}"
    
    def is_active(self):
        """Check if account is currently active"""
        if self.account_status not in ['ACTIVE', 'TRIAL']:
            return False
        if self.expiry_date and self.expiry_date < timezone.now():
            return False
        return True


class Device(models.Model):
    """Registered devices for streaming"""
    DEVICE_TYPES = [
        ('WEB', 'Web Browser'),
        ('MOBILE', 'Mobile App'),
        ('TV', 'Smart TV'),
        ('TABLET', 'Tablet'),
        ('DESKTOP', 'Desktop App'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streaming_devices')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_name = models.CharField(max_length=100)  # User-friendly name
    device_id = models.CharField(max_length=100, unique=True)  # Unique device identifier
    os = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"


class Watchlist(models.Model):
    """User watchlists"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='watchlist_items')
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('profile', 'title')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.profile.name} - {self.title.name}"


class PlaybackHistory(models.Model):
    """Viewing history and progress tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='playback_history')
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True)
    
    position_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField()
    completed_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completed = models.BooleanField(default=False)
    
    # Session info
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['profile', 'updated_at']),
            models.Index(fields=['completed']),
        ]
    
    def __str__(self):
        content = self.episode or self.title
        return f"{self.profile.name} - {content} ({self.completed_percent}%)"


class Rating(models.Model):
    """Content ratings by users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ratings')
    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name='ratings')
    stars = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('profile', 'title')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.profile.name} - {self.title.name} ({self.stars}★)"


class ManualPayment(models.Model):
    """Manual payment recording system"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('PO_INVOICE', 'Purchase Order/Invoice'),
        ('OTHER', 'Other'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('INR', 'Indian Rupee'),
        ('CAD', 'Canadian Dollar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='manual_payments')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_no = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    date_received = models.DateField()
    notes = models.TextField(blank=True)
    receipt_file = models.FileField(upload_to='payment_receipts/', null=True, blank=True)
    
    # Admin tracking
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='recorded_payments', on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_received']
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} ({self.method})"


class Invoice(models.Model):
    """Manual invoice system"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('VOID', 'Void'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    invoice_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    # Dates
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Content
    description = models.TextField()
    notes = models.TextField(blank=True)
    
    # Admin fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_invoices', on_delete=models.SET_NULL, null=True)
    payments = models.ManyToManyField(ManualPayment, blank=True, related_name='invoices')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"INV-{self.invoice_number} - {self.user.email} ({self.status})"
    
    def get_paid_amount(self):
        """Calculate total paid amount from linked payments"""
        return sum(payment.amount for payment in self.payments.all())
    
    def is_fully_paid(self):
        """Check if invoice is fully paid"""
        return self.get_paid_amount() >= self.amount


class ContentAuditLog(models.Model):
    """Audit logging for content and user actions"""
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('UPLOAD', 'Upload'),
        ('DOWNLOAD', 'Download'),
        ('STREAM', 'Stream'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PAYMENT', 'Payment'),
        ('ENTITLEMENT_CHANGE', 'Entitlement Change'),
        ('DEVICE_REGISTER', 'Device Register'),
        ('DEVICE_BLOCK', 'Device Block'),
    ]
    
    ENTITY_TYPES = [
        ('user', 'User'),
        ('title', 'Title'),
        ('episode', 'Episode'),
        ('asset', 'Asset'),
        ('payment', 'Payment'),
        ('invoice', 'Invoice'),
        ('entitlement', 'Entitlement'),
        ('device', 'Device'),
        ('profile', 'Profile'),
        ('watchlist', 'Watchlist'),
        ('rating', 'Rating'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.CharField(max_length=100)
    entity_name = models.CharField(max_length=200, blank=True)  # For easier reading
    
    # Change tracking
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['actor_user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        actor = self.actor_user.email if self.actor_user else 'System'
        return f"{actor} {self.action} {self.entity_type} at {self.timestamp}"


# Enhanced Role and Permission System
class EnhancedRole(models.Model):
    """Enhanced role system with hierarchical permissions"""
    ROLE_TYPES = [
        ('SUPER_ADMIN', 'Super Administrator'),
        ('ADMIN_CUSTOM', 'Custom Administrator'),
        ('CONTENT_MANAGER', 'Content Manager'),
        ('USER_SUPPORT', 'User Support'),
        ('FINANCE_OPS', 'Finance Operations'),
        ('READ_ONLY_AUDITOR', 'Read-Only Auditor'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    is_system = models.BooleanField(default=False)  # Prevents deletion
    parent_role = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    
    # Permission scopes as JSON
    scopes = models.JSONField(default=dict)  # e.g., {"users": ["read", "write"], "content": ["read"]}
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def has_scope(self, resource, action):
        """Check if role has specific scope permission"""
        resource_perms = self.scopes.get(resource, [])
        return action in resource_perms or 'all' in resource_perms


class UserRoleAssignment(models.Model):
    """Many-to-many relationship between users and roles"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(EnhancedRole, on_delete=models.CASCADE, related_name='user_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='role_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'role')
    
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"
