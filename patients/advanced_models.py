from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from patients.models import Patient, Appointment
import json

class PatientAdmission(models.Model):
    """
    Comprehensive patient admission tracking model
    """
    ADMISSION_TYPE_CHOICES = [
        ('emergency', 'Emergency'),
        ('elective', 'Elective'),
        ('outpatient', 'Outpatient'),
        ('observation', 'Observation'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('admitted', 'Admitted'),
        ('in_treatment', 'In Treatment'),
        ('stable', 'Stable'),
        ('critical', 'Critical'),
        ('recovery', 'Recovery'),
        ('discharge_ready', 'Discharge Ready'),
        ('discharged', 'Discharged'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical'),
    ]
    
    # Primary Keys and Relationships
    admission_id = models.CharField(max_length=20, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    attending_physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='patient_admissions'
    )
    
    # Admission Details
    admission_date = models.DateTimeField(default=timezone.now)
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES)
    department = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    bed_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Medical Information
    chief_complaint = models.TextField()
    initial_diagnosis = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    
    # Status and Priority
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admitted')
    priority_level = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Insurance and Billing
    insurance_provider = models.CharField(max_length=200, blank=True, null=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Discharge Information
    discharge_date = models.DateTimeField(blank=True, null=True)
    discharge_diagnosis = models.TextField(blank=True, null=True)
    discharge_instructions = models.TextField(blank=True, null=True)
    discharge_medications = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    
    # AI and Analytics
    ai_risk_score = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )
    ai_predictions = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_admissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-admission_date']
        indexes = [
            models.Index(fields=['admission_id']),
            models.Index(fields=['patient', 'admission_date']),
            models.Index(fields=['current_status']),
            models.Index(fields=['priority_level']),
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.admission_id}"
    
    @property
    def length_of_stay(self):
        """Calculate current length of stay in days"""
        end_date = self.discharge_date or timezone.now()
        delta = end_date - self.admission_date
        return delta.days
    
    @property
    def is_discharged(self):
        return self.current_status == 'discharged' and self.discharge_date is not None

class PatientJourney(models.Model):
    """
    Track complete patient journey from admission to discharge
    """
    JOURNEY_STAGE_CHOICES = [
        ('registration', 'Registration'),
        ('admission', 'Admission'),
        ('triage', 'Triage'),
        ('initial_assessment', 'Initial Assessment'),
        ('diagnosis', 'Diagnosis'),
        ('testing', 'Testing/Procedures'),
        ('treatment', 'Treatment'),
        ('monitoring', 'Monitoring'),
        ('consultation', 'Consultation'),
        ('surgery', 'Surgery'),
        ('recovery', 'Recovery'),
        ('discharge_planning', 'Discharge Planning'),
        ('discharge', 'Discharge'),
    ]
    
    # Relationships
    admission = models.ForeignKey(PatientAdmission, on_delete=models.CASCADE, related_name='journey_events')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='journey_events')
    
    # Journey Details
    stage = models.CharField(max_length=30, choices=JOURNEY_STAGE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200)
    action_taken = models.CharField(max_length=500)
    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='journey_actions'
    )
    
    # Clinical Data
    vital_signs = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)  # File paths, URLs, etc.
    
    # Duration and Metrics
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    wait_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['admission', 'timestamp']),
            models.Index(fields=['patient', 'timestamp']),
            models.Index(fields=['stage']),
        ]
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.stage} at {self.timestamp}"

class AIPatientInsights(models.Model):
    """
    Store AI-generated insights and predictions for patients
    """
    INSIGHT_TYPE_CHOICES = [
        ('risk_assessment', 'Risk Assessment'),
        ('length_of_stay', 'Length of Stay Prediction'),
        ('readmission_risk', 'Readmission Risk'),
        ('complication_risk', 'Complication Risk'),
        ('treatment_recommendation', 'Treatment Recommendation'),
        ('discharge_planning', 'Discharge Planning'),
        ('cost_prediction', 'Cost Prediction'),
    ]
    
    CONFIDENCE_LEVEL_CHOICES = [
        ('low', 'Low (< 70%)'),
        ('medium', 'Medium (70-85%)'),
        ('high', 'High (85-95%)'),
        ('very_high', 'Very High (> 95%)'),
    ]
    
    # Relationships
    admission = models.ForeignKey(PatientAdmission, on_delete=models.CASCADE, related_name='ai_insights')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_insights')
    
    # Insight Details
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPE_CHOICES)
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVEL_CHOICES)
    
    # Predictions and Recommendations
    prediction_data = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    risk_factors = models.JSONField(default=list)
    
    # Scoring
    risk_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Risk score from 0 (low) to 10 (high)"
    )
    accuracy_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model accuracy score from 0 to 1"
    )
    
    # Model Information
    model_version = models.CharField(max_length=50, default="v1.0")
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Validation
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='validated_insights'
    )
    is_validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['admission', 'insight_type']),
            models.Index(fields=['patient', 'insight_type']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.insight_type} (Score: {self.risk_score})"

class PatientReport(models.Model):
    """
    Generate and store comprehensive patient reports
    """
    REPORT_TYPE_CHOICES = [
        ('admission', 'Admission Report'),
        ('clinical_summary', 'Clinical Summary'),
        ('discharge_summary', 'Discharge Summary'),
        ('ai_analysis', 'AI Analysis Report'),
        ('comprehensive', 'Comprehensive Report'),
        ('billing', 'Billing Report'),
        ('quality_metrics', 'Quality Metrics Report'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]
    
    # Relationships
    admission = models.ForeignKey(PatientAdmission, on_delete=models.CASCADE, related_name='reports')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='reports')
    
    # Report Details
    report_id = models.CharField(max_length=50, unique=True, db_index=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    
    # Content
    content = models.JSONField(default=dict)  # Structured report data
    summary = models.TextField(blank=True, null=True)
    
    # File Information
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # in bytes
    file_format = models.CharField(max_length=10, default='PDF')
    
    # Generation Details
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='generated_reports'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    # Access and Security
    is_confidential = models.BooleanField(default=True)
    access_log = models.JSONField(default=list)  # Track who accessed the report
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['admission', 'report_type']),
            models.Index(fields=['patient', 'report_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"
    
    def log_access(self, user, action='viewed'):
        """Log report access for audit trail"""
        access_entry = {
            'user_id': user.id,
            'user_name': user.full_name,
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'ip_address': getattr(user, '_ip_address', None)
        }
        if not isinstance(self.access_log, list):
            self.access_log = []
        self.access_log.append(access_entry)
        self.save(update_fields=['access_log'])

class PatientMetrics(models.Model):
    """
    Store patient care quality metrics and KPIs
    """
    # Relationships
    admission = models.OneToOneField(PatientAdmission, on_delete=models.CASCADE, related_name='metrics')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='metrics')
    
    # Time Metrics
    registration_to_triage_minutes = models.PositiveIntegerField(blank=True, null=True)
    triage_to_doctor_minutes = models.PositiveIntegerField(blank=True, null=True)
    door_to_doctor_minutes = models.PositiveIntegerField(blank=True, null=True)
    diagnosis_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    treatment_start_minutes = models.PositiveIntegerField(blank=True, null=True)
    
    # Clinical Metrics
    vital_signs_frequency = models.PositiveIntegerField(default=0)
    medication_adherence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        blank=True, null=True
    )
    pain_scores = models.JSONField(default=list)  # Track pain scores over time
    
    # Quality Indicators
    hospital_acquired_infections = models.BooleanField(default=False)
    medication_errors = models.PositiveIntegerField(default=0)
    falls_incidents = models.PositiveIntegerField(default=0)
    pressure_ulcers = models.BooleanField(default=False)
    
    # Patient Satisfaction
    satisfaction_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        blank=True, null=True
    )
    complaints_filed = models.PositiveIntegerField(default=0)
    compliments_received = models.PositiveIntegerField(default=0)
    
    # Financial Metrics
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    insurance_coverage_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Outcome Metrics
    readmission_30_days = models.BooleanField(default=False)
    complications_occurred = models.BooleanField(default=False)
    treatment_successful = models.BooleanField(default=True)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"Metrics for {self.patient.full_name} - {self.admission.admission_id}"
