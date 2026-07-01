from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

class AllopathyHospital(models.Model):
    """Hospital/Medical Institution model for S3 data management"""
    
    HOSPITAL_TYPES = [
        ('general', 'General Hospital'),
        ('specialty', 'Specialty Hospital'),
        ('teaching', 'Teaching Hospital'),
        ('research', 'Research Hospital'),
        ('rehabilitation', 'Rehabilitation Center'),
        ('psychiatric', 'Psychiatric Hospital'),
        ('cardiac', 'Cardiac Center'),
        ('cancer', 'Cancer Center'),
        ('trauma', 'Trauma Center'),
        ('pediatric', 'Pediatric Hospital'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    hospital_type = models.CharField(max_length=50, choices=HOSPITAL_TYPES, default='general')
    license_number = models.CharField(max_length=100, unique=True)
    chief_physician = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    bed_capacity = models.PositiveIntegerField(default=0)
    specialties = models.TextField(help_text="Comma-separated list of medical specialties")
    accreditation = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    s3_bucket = models.CharField(max_length=255, blank=True)
    s3_region = models.CharField(max_length=50, default='us-east-1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_hospitals'
        verbose_name = 'Allopathy Hospital'
        verbose_name_plural = 'Allopathy Hospitals'
    
    def __str__(self):
        return f"{self.name} ({self.hospital_type.title()})"

class AllopathyPatientS3(models.Model):
    """Patient model for S3 data management with comprehensive medical information"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('Unknown', 'Unknown'),
    ]
    
    ADMISSION_TYPES = [
        ('outpatient', 'Outpatient'),
        ('inpatient', 'Inpatient'),
        ('emergency', 'Emergency'),
        ('surgery', 'Surgery'),
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('routine_checkup', 'Routine Checkup'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('discharged', 'Discharged'),
        ('admitted', 'Admitted'),
        ('critical', 'Critical'),
        ('stable', 'Stable'),
        ('deceased', 'Deceased'),
        ('transferred', 'Transferred'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(AllopathyHospital, on_delete=models.CASCADE, related_name='patients')
    patient_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, default='Unknown')
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=20)
    admission_date = models.DateTimeField()
    admission_type = models.CharField(max_length=50, choices=ADMISSION_TYPES, default='outpatient')
    attending_physician = models.CharField(max_length=200)
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    allergies = models.TextField(blank=True, help_text="Known allergies")
    current_medications = models.TextField(blank=True, help_text="Current medications")
    medical_history = models.TextField(blank=True, help_text="Previous medical history")
    vital_signs = models.JSONField(default=dict, blank=True, help_text="Latest vital signs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_patients_s3'
        verbose_name = 'Allopathy Patient'
        verbose_name_plural = 'Allopathy Patients'
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AllopathyFile(models.Model):
    """File management model for S3 storage"""
    
    FILE_CATEGORIES = [
        ('lab_results', 'Laboratory Results'),
        ('radiology', 'Radiology Reports'),
        ('pathology', 'Pathology Reports'),
        ('prescriptions', 'Prescriptions'),
        ('discharge_summary', 'Discharge Summary'),
        ('operation_notes', 'Operation Notes'),
        ('consultation_notes', 'Consultation Notes'),
        ('medical_images', 'Medical Images'),
        ('insurance_documents', 'Insurance Documents'),
        ('consent_forms', 'Consent Forms'),
        ('referral_letters', 'Referral Letters'),
        ('progress_notes', 'Progress Notes'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('archived', 'Archived'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(AllopathyHospital, on_delete=models.CASCADE, related_name='files')
    patient = models.ForeignKey(AllopathyPatientS3, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    filename = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=FILE_CATEGORIES)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    file_hash = models.CharField(max_length=64, unique=True)
    s3_key = models.CharField(max_length=500)
    s3_bucket = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    download_url = models.URLField(blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_confidential = models.BooleanField(default=True)
    access_level = models.CharField(max_length=50, default='restricted')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_files'
        verbose_name = 'Allopathy File'
        verbose_name_plural = 'Allopathy Files'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['upload_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.original_name} ({self.category})"
    
    @property
    def patient_name(self):
        return self.patient.full_name if self.patient else "Unknown"

class AllopathyAnalysis(models.Model):
    """AI Analysis model for medical data processing"""
    
    ANALYSIS_TYPES = [
        ('lab_analysis', 'Laboratory Analysis'),
        ('radiology_analysis', 'Radiology Analysis'),
        ('symptom_analysis', 'Symptom Analysis'),
        ('drug_interaction', 'Drug Interaction Check'),
        ('diagnosis_suggestion', 'Diagnosis Suggestion'),
        ('treatment_recommendation', 'Treatment Recommendation'),
        ('prognosis_prediction', 'Prognosis Prediction'),
        ('risk_assessment', 'Risk Assessment'),
        ('vitals_analysis', 'Vital Signs Analysis'),
        ('ecg_analysis', 'ECG Analysis'),
        ('pathology_detection', 'Pathology Detection'),
        ('clinical_decision_support', 'Clinical Decision Support'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(AllopathyHospital, on_delete=models.CASCADE, related_name='analyses')
    patient = models.ForeignKey(AllopathyPatientS3, on_delete=models.CASCADE, related_name='analyses')
    file = models.ForeignKey(AllopathyFile, on_delete=models.CASCADE, related_name='analyses', null=True, blank=True)
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)
    input_data = models.JSONField(default=dict, help_text="Input data for analysis")
    results = models.JSONField(default=dict, help_text="Analysis results")
    confidence_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    recommendations = models.TextField(blank=True)
    risk_factors = models.JSONField(default=list, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_analyses')
    review_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_time = models.DurationField(null=True, blank=True)
    ai_model_version = models.CharField(max_length=50, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_analyses'
        verbose_name = 'Allopathy Analysis'
        verbose_name_plural = 'Allopathy Analyses'
        indexes = [
            models.Index(fields=['analysis_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.analysis_type} - {self.patient.full_name}"
    
    @property
    def patient_name(self):
        return self.patient.full_name
    
    @property
    def file_name(self):
        return self.file.original_name if self.file else "N/A"

class AllopathyMedicalRecord(models.Model):
    """Comprehensive medical record model"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('transferred', 'Transferred'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(AllopathyPatientS3, on_delete=models.CASCADE, related_name='medical_records')
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True, blank=True)
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField()
    past_medical_history = models.TextField()
    family_history = models.TextField(blank=True)
    social_history = models.TextField(blank=True)
    review_of_systems = models.TextField(blank=True)
    physical_examination = models.TextField()
    assessment_and_plan = models.TextField()
    attending_physician = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, blank=True)
    diagnosis_codes = models.JSONField(default=list, help_text="ICD-10 diagnosis codes")
    procedures = models.JSONField(default=list, help_text="Procedures performed")
    lab_orders = models.JSONField(default=list, help_text="Laboratory orders")
    imaging_orders = models.JSONField(default=list, help_text="Imaging orders")
    consultations = models.JSONField(default=list, help_text="Consultations requested")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_medical_records'
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.admission_date.strftime('%Y-%m-%d')}"

class AllopathyTreatmentPlan(models.Model):
    """Treatment plan model for patient care management"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('modified', 'Modified'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(AllopathyPatientS3, on_delete=models.CASCADE, related_name='treatment_plans')
    medical_record = models.ForeignKey(AllopathyMedicalRecord, on_delete=models.CASCADE, related_name='treatment_plans', null=True, blank=True)
    plan_date = models.DateField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    medications = models.JSONField(default=list, help_text="Prescribed medications")
    procedures_planned = models.JSONField(default=list, help_text="Planned procedures")
    follow_up_instructions = models.TextField()
    diet_instructions = models.TextField(blank=True)
    activity_restrictions = models.TextField(blank=True)
    prescribed_by = models.CharField(max_length=200)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    expected_duration = models.DurationField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    goals = models.TextField(help_text="Treatment goals and expected outcomes")
    contraindications = models.TextField(blank=True)
    monitoring_parameters = models.JSONField(default=list, help_text="Parameters to monitor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'allopathy_treatment_plans'
        verbose_name = 'Treatment Plan'
        verbose_name_plural = 'Treatment Plans'
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.diagnosis[:50]}..."
