from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings # For ForeignKey to CustomUser

# Import notification models
from .notification_models import *

class CustomUserManager(DjangoUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        # Ensure username is set if your AbstractUser expects it.
        # If username is still used, ensure it's unique or derive it from email.
        username = extra_fields.pop('username', None)
        if not username:
            base_username = email.split('@')[0]
            username_candidate = base_username
            counter = 1
            # Check against the actual model using self.model
            while self.model.objects.filter(username=username_candidate).exists():
                username_candidate = f"{base_username}{counter}"
                counter += 1
            username = username_candidate
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        # Username is required by AbstractUser, ensure it's passed or derived
        if 'username' not in extra_fields and not email.split('@')[0]:
             raise ValueError("Superuser must have a username.")
        elif 'username' not in extra_fields:
            extra_fields['username'] = email.split('@')[0] # Default username to email prefix

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
        ('pharmacist', 'Pharmacist'),
    ]
    
    # Override the groups and user_permissions fields to fix related_name conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name='hospital_customuser_set',
        related_query_name='hospital_customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='hospital_customuser_set',
        related_query_name='hospital_customuser',
    )
    
    # username is inherited from AbstractUser, unique=True by default.
    # We auto-generate it if not provided, but email is the login field.
    email = models.EmailField(_('email address'), unique=True) # Email is the login identifier
    full_name = models.CharField(max_length=100) # As per Tables.txt (VARCHAR(100) implies NOT NULL)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True, help_text="Medical license for doctors")
    certification = models.CharField(max_length=100, blank=True, null=True, help_text="Certification for nurses")
    specialization = models.CharField(max_length=100, blank=True, null=True, help_text="Medical specialization for doctors")
    is_verified = models.BooleanField(default=False, help_text="Email verification status")
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Password management fields
    password_change_required = models.BooleanField(default=False, help_text="Force password change on next login")
    first_login_completed = models.BooleanField(default=False, help_text="Whether user has completed first login setup")
    password_changed_at = models.DateTimeField(null=True, blank=True, help_text="Last password change timestamp")
    temp_password_expires = models.DateTimeField(null=True, blank=True, help_text="Temporary password expiration")
    failed_login_attempts = models.PositiveIntegerField(default=0, help_text="Failed login attempt counter")
    account_locked_until = models.DateTimeField(null=True, blank=True, help_text="Account lockout expiration")
    
    # is_active is inherited from AbstractUser (default=True)
    # date_joined (for created_at) is inherited from AbstractUser (default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name'] # username is required by AbstractUser, full_name by Tables.txt

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def set_password(self, raw_password):
        """Override set_password to track password changes"""
        super().set_password(raw_password)
        self.password_changed_at = timezone.now()
        self.password_change_required = False
        self.first_login_completed = True
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def require_password_change(self, expires_in_hours=24):
        """Mark user as requiring password change"""
        self.password_change_required = True
        self.temp_password_expires = timezone.now() + timezone.timedelta(hours=expires_in_hours)
        self.first_login_completed = False
        
    def is_password_expired(self):
        """Check if temporary password has expired"""
        if self.temp_password_expires:
            return timezone.now() > self.temp_password_expires
        return False
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            if timezone.now() < self.account_locked_until:
                return True
            else:
                # Auto-unlock expired lockouts
                self.account_locked_until = None
                self.failed_login_attempts = 0
                self.save()
        return False
    
    def increment_failed_login(self, lockout_threshold=3, lockout_minutes=15):
        """Track failed login attempts and lock account if needed"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= lockout_threshold:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
        self.save()
    
    def reset_failed_logins(self):
        """Reset failed login counter on successful login"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()
    
    def needs_first_login_setup(self):
        """Check if user needs to complete first login setup"""
        return not self.first_login_completed or self.password_change_required

class StaffProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='staffprofile')
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    join_date = models.DateField(blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Staff Profile for {self.user.email}"

class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='patientprofile')
    date_of_birth = models.DateField(blank=True, null=True)
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        # Add more if needed, or leave as CharField if free-form
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True) # e.g., A+, O-
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True) # Consider a more structured approach if history is complex (e.g., JSONField or separate model)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patient Profile for {self.user.email}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='doctor_appointments',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'} # Ensures only users with role 'doctor' can be selected
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='patient_appointments',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'} # Ensures only users with role 'patient' can be selected
    )
    appointment_date = models.DateTimeField() # NOT NULL
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled') # NOT NULL with DEFAULT
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.patient.full_name} with Dr. {self.doctor.full_name} on {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"

class IncomeReport(models.Model):
    INCOME_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    date = models.DateField() # NOT NULL
    income_amount = models.DecimalField(max_digits=10, decimal_places=2) # NOT NULL
    income_type = models.CharField(max_length=20, choices=INCOME_TYPE_CHOICES) # NOT NULL
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, # Allows NULL as per ON DELETE SET NULL
        related_name='recorded_income_reports'
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_income_type_display()} Income Report for {self.date}: {self.income_amount}"

class Survey(models.Model):
    METRIC_TYPE_CHOICES = [
        ('income_growth', 'Income Growth'),
        ('patient_satisfaction', 'Patient Satisfaction'),
        ('staff_performance', 'Staff Performance'),
        ('bed_occupancy', 'Bed Occupancy'),
    ]
    survey_name = models.CharField(max_length=100) # NOT NULL
    period_start = models.DateField() # NOT NULL
    period_end = models.DateField() # NOT NULL
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES) # NOT NULL
    value = models.DecimalField(max_digits=6, decimal_places=2) # NOT NULL
    unit = models.CharField(max_length=20, default='%') # NOT NULL with DEFAULT
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.survey_name} - {self.get_metric_type_display()}"


class FeatureAccess(models.Model):
    """Model to manage user access to different healthcare features/modules"""
    
    FEATURE_CHOICES = [
        ('medicine', 'General Medicine'),
        ('dentistry', 'Dentistry'),
        ('dermatology', 'Dermatology'),
        ('pathology', 'Pathology'),
        ('radiology', 'Radiology'),
        ('patients', 'Patient Management'),
        ('subscriptions', 'Subscription Management'),
        ('hospital', 'Hospital Management'),
        ('secureneat', 'SecureNeat Security'),
        ('appointments', 'Appointment Scheduling'),
        ('billing', 'Billing & Payments'),
        ('reports', 'Reports & Analytics'),
        ('emergency', 'Emergency Services'),
        ('pharmacy', 'Pharmacy Management'),
        ('lab_tests', 'Laboratory Tests'),
        ('imaging', 'Medical Imaging'),
        ('telemedicine', 'Telemedicine'),
        ('ai_diagnosis', 'AI-Powered Diagnosis'),
        ('diabetes_management', 'Diabetes Management'),
        ('cancer_detection', 'Cancer Detection'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feature_access')
    feature = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'feature')
        verbose_name = 'Feature Access'
        verbose_name_plural = 'Feature Access'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_feature_display()}"


class UserFeatureProfile(models.Model):
    """User profile for managing selected features during user creation"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feature_profile')
    selected_features = models.JSONField(default=list, help_text="List of selected feature codes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feature Profile for {self.user.email}"
    
    def get_enabled_features(self):
        """Get list of enabled features for this user"""
        return self.user.feature_access.filter(is_enabled=True).values_list('feature', flat=True)


class AdminPermissions(models.Model):
    """Model to store custom permissions for admin users"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_permissions')
    can_manage_users = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=True)
    can_manage_departments = models.BooleanField(default=True)
    can_access_billing = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    can_access_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Admin Permissions for {self.user.email}"


class AdminDashboardFeatures(models.Model):
    """Model to store dashboard feature access for admin users"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_features')
    
    # User Management Features
    user_management = models.BooleanField(default=True)
    patient_management = models.BooleanField(default=True)
    doctor_management = models.BooleanField(default=False)
    nurse_management = models.BooleanField(default=False)
    pharmacist_management = models.BooleanField(default=False)
    
    # Healthcare Management Features
    hospital_management = models.BooleanField(default=False)
    clinic_management = models.BooleanField(default=False)
    all_doctors = models.BooleanField(default=False)
    add_doctors = models.BooleanField(default=False)
    doctor_profile = models.BooleanField(default=False)
    
    # Medical Modules
    medicine_module = models.BooleanField(default=False)
    dentistry_module = models.BooleanField(default=False)
    dermatology_module = models.BooleanField(default=False)
    pathology_module = models.BooleanField(default=False)
    radiology_module = models.BooleanField(default=False)
    homeopathy_module = models.BooleanField(default=False)
    allopathy_module = models.BooleanField(default=False)
    cosmetology_module = models.BooleanField(default=False)
    dna_sequencing_module = models.BooleanField(default=False)
    secureneat_module = models.BooleanField(default=False)
    
    # Administrative Features
    subscription_management = models.BooleanField(default=False)
    billing_reports = models.BooleanField(default=False)
    financial_dashboard = models.BooleanField(default=False)
    system_settings = models.BooleanField(default=False)
    audit_logs = models.BooleanField(default=False)
    
    # Analytics Features
    user_analytics = models.BooleanField(default=True)
    medical_reports = models.BooleanField(default=False)
    revenue_reports = models.BooleanField(default=False)
    appointment_analytics = models.BooleanField(default=False)
    inventory_reports = models.BooleanField(default=False)
    
    # Action Features
    create_user = models.BooleanField(default=True)
    schedule_appointment = models.BooleanField(default=False)
    generate_report = models.BooleanField(default=True)
    backup_system = models.BooleanField(default=False)
    send_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard Features for {self.user.email}"


class UserCreationQuota(models.Model):
    """Model to store user creation quota limits for admin users"""
    
    RESET_PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('never', 'Never'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='creation_quota')
    enabled = models.BooleanField(default=True, help_text="Whether quota limits are enabled")
    
    # Maximum limits
    max_total_users = models.PositiveIntegerField(default=50)
    max_doctors = models.PositiveIntegerField(default=10)
    max_nurses = models.PositiveIntegerField(default=15)
    max_patients = models.PositiveIntegerField(default=20)
    max_pharmacists = models.PositiveIntegerField(default=5)
    
    # Reset configuration
    quota_reset_period = models.CharField(max_length=20, choices=RESET_PERIOD_CHOICES, default='monthly')
    last_reset = models.DateTimeField(default=timezone.now)
    
    # Current usage tracking
    current_total_users = models.PositiveIntegerField(default=0)
    current_doctors = models.PositiveIntegerField(default=0)
    current_nurses = models.PositiveIntegerField(default=0)
    current_patients = models.PositiveIntegerField(default=0)
    current_pharmacists = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Creation Quota for {self.user.email}"
    
    def can_create_user(self, role):
        """Check if user can create a new user of specified role"""
        if not self.enabled:
            return True
        
        if self.current_total_users >= self.max_total_users:
            return False
        
        role_limits = {
            'doctor': (self.current_doctors, self.max_doctors),
            'nurse': (self.current_nurses, self.max_nurses),
            'patient': (self.current_patients, self.max_patients),
            'pharmacist': (self.current_pharmacists, self.max_pharmacists),
        }
        
        if role in role_limits:
            current, max_limit = role_limits[role]
            return current < max_limit
        
        return True
    
    def increment_usage(self, role):
        """Increment usage counters when a user is created"""
        self.current_total_users += 1
        
        if role == 'doctor':
            self.current_doctors += 1
        elif role == 'nurse':
            self.current_nurses += 1
        elif role == 'patient':
            self.current_patients += 1
        elif role == 'pharmacist':
            self.current_pharmacists += 1
        
        self.save()
    
    def reset_quota_if_needed(self):
        """Reset quota counters if reset period has passed"""
        now = timezone.now()
        
        if self.quota_reset_period == 'never':
            return
        
        should_reset = False
        
        if self.quota_reset_period == 'monthly':
            # Reset if it's been more than a month
            if (now - self.last_reset).days >= 30:
                should_reset = True
        elif self.quota_reset_period == 'yearly':
            # Reset if it's been more than a year
            if (now - self.last_reset).days >= 365:
                should_reset = True
        
        if should_reset:
            self.current_total_users = 0
            self.current_doctors = 0
            self.current_nurses = 0
            self.current_patients = 0
            self.current_pharmacists = 0
            self.last_reset = now
            self.save()