from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class Patient(models.Model):
    """Extended patient model for dental care"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dental_patient')
    patient_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=15)
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.patient_id}"

    class Meta:
        db_table = 'dentistry_patients'

class Dentist(models.Model):
    """Dentist profile model"""
    SPECIALIZATION_CHOICES = [
        ('general', 'General Dentistry'),
        ('orthodontics', 'Orthodontics'),
        ('oral_surgery', 'Oral Surgery'),
        ('periodontics', 'Periodontics'),
        ('endodontics', 'Endodontics'),
        ('prosthodontics', 'Prosthodontics'),
        ('pediatric', 'Pediatric Dentistry'),
        ('oral_pathology', 'Oral Pathology'),
        ('oral_medicine', 'Oral Medicine'),
        ('cosmetic', 'Cosmetic Dentistry'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dentist_profile')
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, default='general')
    years_experience = models.PositiveIntegerField(default=0)
    education = models.TextField()
    certifications = models.TextField(blank=True)
    clinic_address = models.TextField()
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                                validators=[MinValueValidator(0.00), MaxValueValidator(5.00)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"

    class Meta:
        db_table = 'dentistry_dentists'

class DentalHistory(models.Model):
    """Comprehensive dental history for patients"""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='dental_history')
    
    # Oral Hygiene Habits
    brushing_frequency = models.PositiveIntegerField(default=2, help_text="Times per day")
    flossing_frequency = models.PositiveIntegerField(default=1, help_text="Times per day")
    mouthwash_use = models.BooleanField(default=False)
    
    # Habits and Lifestyle
    smoking = models.BooleanField(default=False)
    alcohol_consumption = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('occasional', 'Occasional'),
        ('moderate', 'Moderate'),
        ('heavy', 'Heavy')
    ], default='none')
    teeth_grinding = models.BooleanField(default=False)
    nail_biting = models.BooleanField(default=False)
    
    # Previous Dental Issues
    previous_orthodontics = models.BooleanField(default=False)
    previous_oral_surgery = models.BooleanField(default=False)
    gum_disease_history = models.BooleanField(default=False)
    tooth_sensitivity = models.BooleanField(default=False)
    
    # Family History
    family_gum_disease = models.BooleanField(default=False)
    family_tooth_loss = models.BooleanField(default=False)
    family_oral_cancer = models.BooleanField(default=False)
    
    # Additional Notes
    chief_complaint = models.TextField(blank=True)
    dental_anxiety_level = models.PositiveIntegerField(default=1, 
                                                      validators=[MinValueValidator(1), MaxValueValidator(10)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dental History - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_dental_history'

class Appointment(models.Model):
    """Dental appointment scheduling"""
    APPOINTMENT_STATUS = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    APPOINTMENT_TYPE = [
        ('consultation', 'Consultation'),
        ('cleaning', 'Cleaning'),
        ('filling', 'Filling'),
        ('extraction', 'Extraction'),
        ('root_canal', 'Root Canal'),
        ('crown', 'Crown'),
        ('bridge', 'Bridge'),
        ('implant', 'Implant'),
        ('orthodontic', 'Orthodontic'),
        ('emergency', 'Emergency'),
        ('follow_up', 'Follow-up'),
    ]

    appointment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    duration = models.PositiveIntegerField(default=30, help_text="Duration in minutes")
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE)
    status = models.CharField(max_length=15, choices=APPOINTMENT_STATUS, default='scheduled')
    chief_complaint = models.TextField()
    notes = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        db_table = 'dentistry_appointments'
        ordering = ['-appointment_date']

class Treatment(models.Model):
    """Dental treatment records"""
    TREATMENT_STATUS = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    treatment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='treatments')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='treatments')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='treatments', null=True, blank=True)
    
    treatment_name = models.CharField(max_length=200)
    treatment_code = models.CharField(max_length=20)  # ADA codes
    tooth_number = models.CharField(max_length=10, blank=True)  # Universal numbering system
    surface = models.CharField(max_length=10, blank=True)  # MODBL surfaces
    
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    procedure_notes = models.TextField(blank=True)
    materials_used = models.TextField(blank=True)
    
    status = models.CharField(max_length=15, choices=TREATMENT_STATUS, default='planned')
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    insurance_coverage = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    patient_payment = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    complications = models.TextField(blank=True)
    post_treatment_instructions = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.treatment_name} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_treatments'
        ordering = ['-start_date']

class DentalXray(models.Model):
    """Dental X-ray and imaging records"""
    XRAY_TYPE = [
        ('periapical', 'Periapical'),
        ('bitewing', 'Bitewing'),
        ('panoramic', 'Panoramic'),
        ('cephalometric', 'Cephalometric'),
        ('cbct', 'CBCT'),
        ('occlusal', 'Occlusal'),
    ]

    xray_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='xrays')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='xrays')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='xrays', null=True, blank=True)
    
    xray_type = models.CharField(max_length=20, choices=XRAY_TYPE)
    tooth_region = models.CharField(max_length=50, blank=True)
    image_file = models.FileField(upload_to='dental_xrays/%Y/%m/')
    
    findings = models.TextField()
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    radiation_dose = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    image_quality = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ], default='good')
    
    taken_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_xray_type_display()} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_xrays'
        ordering = ['-taken_date']

class PeriodontalChart(models.Model):
    """Periodontal charting for gum health assessment"""
    chart_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='periodontal_charts')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='periodontal_charts')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='periodontal_charts', null=True, blank=True)
    
    chart_date = models.DateField(default=timezone.now)
    
    # Periodontal measurements (JSON field for all teeth measurements)
    probing_depths = models.JSONField(default=dict, help_text="Probing depths for all teeth")
    bleeding_on_probing = models.JSONField(default=dict, help_text="Bleeding points")
    plaque_index = models.JSONField(default=dict, help_text="Plaque accumulation")
    mobility = models.JSONField(default=dict, help_text="Tooth mobility")
    recession = models.JSONField(default=dict, help_text="Gingival recession")
    
    overall_periodontal_status = models.CharField(max_length=25, choices=[
        ('healthy', 'Healthy'),
        ('gingivitis', 'Gingivitis'),
        ('mild_periodontitis', 'Mild Periodontitis'),
        ('moderate_periodontitis', 'Moderate Periodontitis'),
        ('severe_periodontitis', 'Severe Periodontitis'),
    ], default='healthy')
    
    treatment_recommendations = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Periodontal Chart - {self.patient.user.get_full_name()} ({self.chart_date})"

    class Meta:
        db_table = 'dentistry_periodontal_charts'
        ordering = ['-chart_date']


class CancerDetection(models.Model):
    """Advanced AI-powered cancer detection records"""
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    DETECTION_STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('under_analysis', 'Under Analysis'),
        ('reviewed', 'Reviewed'),
        ('confirmed', 'Confirmed'),
        ('false_positive', 'False Positive'),
        ('requires_biopsy', 'Requires Biopsy'),
        ('biopsy_scheduled', 'Biopsy Scheduled'),
        ('treatment_planned', 'Treatment Planned'),
    ]
    
    CANCER_TYPE_CHOICES = [
        ('squamous_cell_carcinoma', 'Squamous Cell Carcinoma'),
        ('basal_cell_carcinoma', 'Basal Cell Carcinoma'),
        ('adenocarcinoma', 'Adenocarcinoma'),
        ('melanoma', 'Melanoma'),
        ('lymphoma', 'Lymphoma'),
        ('sarcoma', 'Sarcoma'),
        ('unknown', 'Unknown Type'),
    ]
    
    GRADE_CHOICES = [
        ('well_differentiated', 'Well Differentiated (Grade 1)'),
        ('moderately_differentiated', 'Moderately Differentiated (Grade 2)'),
        ('poorly_differentiated', 'Poorly Differentiated (Grade 3)'),
        ('undifferentiated', 'Undifferentiated (Grade 4)'),
    ]

    detection_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='cancer_detections')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='cancer_detections')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='cancer_detections', null=True, blank=True)
    
    # Detection Details
    detected_at = models.DateTimeField(auto_now_add=True)
    analysis_type = models.CharField(max_length=50, default='oral_cancer_screening')
    ai_model_version = models.CharField(max_length=50, default='CancerDetectionAI-v3.2.1')
    processing_time_ms = models.IntegerField(help_text="AI processing time in milliseconds")
    
    # Cancer Analysis Results
    cancer_detected = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=15, choices=RISK_LEVEL_CHOICES, default='low')
    overall_confidence = models.DecimalField(
        max_digits=5, decimal_places=3,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)],
        help_text="AI confidence score (0.000-1.000)"
    )
    cancer_probability = models.DecimalField(
        max_digits=5, decimal_places=3,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)],
        help_text="Probability of malignancy (0.000-1.000)"
    )
    
    # Cancer Characteristics
    predicted_cancer_type = models.CharField(max_length=30, choices=CANCER_TYPE_CHOICES, blank=True, null=True)
    predicted_stage = models.CharField(max_length=20, blank=True, help_text="TNM staging (e.g., T2N0M0)")
    predicted_grade = models.CharField(max_length=25, choices=GRADE_CHOICES, blank=True, null=True)
    invasion_depth_mm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    lymphovascular_invasion = models.BooleanField(null=True, blank=True)
    perineural_invasion = models.BooleanField(null=True, blank=True)
    
    # Analysis Results (JSON fields for complex data)
    suspicious_areas = models.JSONField(default=list, help_text="List of suspicious areas detected")
    cellular_analysis = models.JSONField(default=dict, help_text="Cellular morphology analysis")
    molecular_markers = models.JSONField(default=dict, help_text="Predicted molecular markers")
    risk_factors = models.JSONField(default=list, help_text="Patient risk factors")
    
    # Clinical Integration
    status = models.CharField(max_length=20, choices=DETECTION_STATUS_CHOICES, default='pending_review')
    reviewed_by = models.ForeignKey(Dentist, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_cancer_detections')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    clinical_notes = models.TextField(blank=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    # Notification Status
    notification_sent = models.BooleanField(default=False)
    notification_priority = models.CharField(max_length=15, default='routine')
    acknowledged_by = models.ManyToManyField(Dentist, through='CancerDetectionAcknowledgment', related_name='acknowledged_detections')
    
    # Treatment Integration
    biopsy_recommended = models.BooleanField(default=False)
    biopsy_scheduled = models.BooleanField(default=False)
    specialist_referral_sent = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cancer Detection {self.detection_id} - {self.patient.user.get_full_name()} ({self.risk_level})"

    class Meta:
        db_table = 'dentistry_cancer_detections'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['cancer_detected', 'risk_level']),
            models.Index(fields=['status', 'detected_at']),
            models.Index(fields=['patient', '-detected_at']),
        ]


class CancerDetectionImage(models.Model):
    """Images associated with cancer detection"""
    IMAGE_TYPE_CHOICES = [
        ('intraoral_photo', 'Intraoral Photography'),
        ('extraoral_photo', 'Extraoral Photography'),
        ('fluorescence_imaging', 'Fluorescence Imaging'),
        ('dermoscopy', 'Dermoscopy'),
        ('biopsy_image', 'Biopsy Image'),
        ('histopathology', 'Histopathology'),
        ('radiograph', 'Radiograph'),
        ('ct_scan', 'CT Scan'),
        ('mri_scan', 'MRI Scan'),
    ]

    image_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cancer_detection = models.ForeignKey(CancerDetection, on_delete=models.CASCADE, related_name='images')
    
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES)
    original_image = models.FileField(upload_to='cancer_detection/original/%Y/%m/')
    processed_image = models.FileField(upload_to='cancer_detection/processed/%Y/%m/', null=True, blank=True)
    thumbnail = models.FileField(upload_to='cancer_detection/thumbnails/%Y/%m/', null=True, blank=True)
    
    # Image Analysis Results
    ai_annotations = models.JSONField(default=dict, help_text="AI-generated annotations and markings")
    regions_of_interest = models.JSONField(default=list, help_text="Suspicious regions identified")
    image_quality_score = models.DecimalField(
        max_digits=5, decimal_places=3,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)],
        null=True, blank=True
    )
    
    # Metadata
    camera_settings = models.JSONField(default=dict, blank=True)
    lighting_conditions = models.CharField(max_length=50, blank=True)
    image_resolution = models.CharField(max_length=20, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_image_type_display()} - {self.cancer_detection.detection_id}"

    class Meta:
        db_table = 'dentistry_cancer_detection_images'
        ordering = ['-uploaded_at']


class CancerDetectionAcknowledgment(models.Model):
    """Tracking acknowledgment of cancer detection alerts by medical staff"""
    acknowledgment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cancer_detection = models.ForeignKey(CancerDetection, on_delete=models.CASCADE)
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE)
    
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    acknowledgment_method = models.CharField(max_length=20, choices=[
        ('dashboard', 'Dashboard'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('mobile_app', 'Mobile App'),
        ('direct_review', 'Direct Review'),
    ], default='dashboard')
    
    notes = models.TextField(blank=True)
    action_taken = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'dentistry_cancer_detection_acknowledgments'
        unique_together = ['cancer_detection', 'dentist']


class CancerRiskAssessment(models.Model):
    """Comprehensive cancer risk assessment for patients"""
    assessment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='cancer_risk_assessments')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='cancer_risk_assessments')
    
    assessment_date = models.DateTimeField(auto_now_add=True)
    
    # Risk Factors Assessment
    age_risk_score = models.IntegerField(default=0)
    tobacco_risk_score = models.IntegerField(default=0)
    alcohol_risk_score = models.IntegerField(default=0)
    family_history_score = models.IntegerField(default=0)
    hpv_exposure_score = models.IntegerField(default=0)
    sun_exposure_score = models.IntegerField(default=0)
    immunosuppression_score = models.IntegerField(default=0)
    previous_lesions_score = models.IntegerField(default=0)
    
    total_risk_score = models.IntegerField(default=0)
    risk_category = models.CharField(max_length=15, choices=[
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk'),
    ], default='low')
    
    # Risk Percentages
    lifetime_risk_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    five_year_risk_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Recommendations
    screening_interval_months = models.IntegerField(default=12)
    next_screening_date = models.DateField()
    preventive_measures = models.JSONField(default=list)
    lifestyle_modifications = models.JSONField(default=list)
    
    # Risk Factor Details (JSON)
    detailed_risk_factors = models.JSONField(default=list)
    environmental_factors = models.JSONField(default=list)
    genetic_factors = models.JSONField(default=list)
    
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cancer Risk Assessment - {self.patient.user.get_full_name()} ({self.risk_category})"

    class Meta:
        db_table = 'dentistry_cancer_risk_assessments'
        ordering = ['-assessment_date']


class CancerTreatmentPlan(models.Model):
    """Treatment planning for confirmed cancer cases"""
    TREATMENT_TYPE_CHOICES = [
        ('surgical_resection', 'Surgical Resection'),
        ('radiation_therapy', 'Radiation Therapy'),
        ('chemotherapy', 'Chemotherapy'),
        ('immunotherapy', 'Immunotherapy'),
        ('targeted_therapy', 'Targeted Therapy'),
        ('combined_therapy', 'Combined Therapy'),
        ('palliative_care', 'Palliative Care'),
        ('active_surveillance', 'Active Surveillance'),
    ]
    
    TREATMENT_STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('modified', 'Modified'),
        ('discontinued', 'Discontinued'),
    ]

    plan_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cancer_detection = models.ForeignKey(CancerDetection, on_delete=models.CASCADE, related_name='treatment_plans')
    primary_dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='primary_cancer_plans')
    
    created_at = models.DateTimeField(auto_now_add=True)
    planned_start_date = models.DateField()
    estimated_duration_weeks = models.IntegerField()
    
    # Primary Treatment
    primary_treatment_type = models.CharField(max_length=25, choices=TREATMENT_TYPE_CHOICES)
    treatment_description = models.TextField()
    treatment_goals = models.TextField()
    expected_outcomes = models.TextField()
    
    # Treatment Team
    multidisciplinary_team = models.JSONField(default=list, help_text="List of specialists involved")
    lead_oncologist = models.CharField(max_length=200, blank=True)
    surgeon = models.CharField(max_length=200, blank=True)
    radiation_oncologist = models.CharField(max_length=200, blank=True)
    
    # Treatment Options
    treatment_options = models.JSONField(default=list, help_text="Available treatment options")
    recommended_option = models.CharField(max_length=100)
    alternative_options = models.JSONField(default=list)
    
    # Prognosis
    success_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    five_year_survival_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recurrence_risk_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Follow-up Protocol
    follow_up_schedule = models.JSONField(default=dict)
    monitoring_biomarkers = models.JSONField(default=list)
    imaging_schedule = models.JSONField(default=dict)
    
    # Status and Progress
    status = models.CharField(max_length=20, choices=TREATMENT_STATUS_CHOICES, default='proposed')
    patient_consent_obtained = models.BooleanField(default=False)
    treatment_commenced = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Outcomes and Complications
    treatment_response = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    quality_of_life_impact = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Treatment Plan {self.plan_id} - {self.cancer_detection.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_cancer_treatment_plans'
        ordering = ['-created_at']


class CancerNotification(models.Model):
    """Notification system for cancer detection alerts"""
    NOTIFICATION_TYPE_CHOICES = [
        ('cancer_detection_alert', 'Cancer Detection Alert'),
        ('high_risk_patient', 'High Risk Patient'),
        ('biopsy_reminder', 'Biopsy Reminder'),
        ('follow_up_due', 'Follow-up Due'),
        ('treatment_update', 'Treatment Update'),
        ('emergency_alert', 'Emergency Alert'),
    ]
    
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('acknowledged', 'Acknowledged'),
        ('expired', 'Expired'),
    ]

    notification_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cancer_detection = models.ForeignKey(CancerDetection, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='routine')
    
    # Recipients
    recipient_dentists = models.ManyToManyField(Dentist, related_name='cancer_notifications')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='cancer_notifications', null=True, blank=True)
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_required = models.TextField(blank=True)
    recommended_actions = models.JSONField(default=list)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Delivery Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery Methods
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_notification_sent = models.BooleanField(default=False)
    dashboard_alert = models.BooleanField(default=True)
    
    # Additional Data
    metadata = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.priority} ({self.status})"

    class Meta:
        db_table = 'dentistry_cancer_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

class DentalAIAnalysis(models.Model):
    """AI-powered dental analysis and diagnosis assistance"""
    ANALYSIS_TYPE = [
        ('xray_analysis', 'X-ray Analysis'),
        ('cavity_detection', 'Cavity Detection'),
        ('periodontal_assessment', 'Periodontal Assessment'),
        ('orthodontic_analysis', 'Orthodontic Analysis'),
        ('oral_cancer_screening', 'Oral Cancer Screening'),
        ('treatment_planning', 'Treatment Planning'),
        ('risk_assessment', 'Risk Assessment'),
    ]

    AI_CONFIDENCE_LEVEL = [
        ('very_low', 'Very Low (0-20%)'),
        ('low', 'Low (21-40%)'),
        ('moderate', 'Moderate (41-60%)'),
        ('high', 'High (61-80%)'),
        ('very_high', 'Very High (81-100%)'),
    ]

    analysis_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_analyses')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='ai_analyses')
    
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPE)
    input_image = models.FileField(upload_to='dental_ai_input/%Y/%m/', null=True, blank=True)
    processed_image = models.FileField(upload_to='dental_ai_output/%Y/%m/', null=True, blank=True)
    
    # AI Analysis Results
    ai_findings = models.JSONField(default=dict, help_text="Structured AI findings")
    confidence_level = models.CharField(max_length=15, choices=AI_CONFIDENCE_LEVEL)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                   validators=[MinValueValidator(0.00), MaxValueValidator(100.00)])
    
    detected_conditions = models.JSONField(default=list, help_text="List of detected conditions")
    treatment_suggestions = models.JSONField(default=list, help_text="AI-generated treatment suggestions")
    differential_diagnosis = models.JSONField(default=list, help_text="Differential diagnosis options")
    
    # Clinical Integration
    dentist_review = models.TextField(blank=True, help_text="Dentist's review of AI analysis")
    approved_by_dentist = models.BooleanField(default=False)
    clinical_notes = models.TextField(blank=True)
    
    # Technical Details
    ai_model_version = models.CharField(max_length=50, default="DentalAI-v1.0")
    processing_time = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI {self.get_analysis_type_display()} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_ai_analyses'
        ordering = ['-created_at']

class Prescription(models.Model):
    """Dental prescriptions"""
    MEDICATION_TYPE = [
        ('antibiotic', 'Antibiotic'),
        ('painkiller', 'Painkiller'),
        ('anti_inflammatory', 'Anti-inflammatory'),
        ('mouthwash', 'Mouthwash'),
        ('fluoride', 'Fluoride'),
        ('other', 'Other'),
    ]

    prescription_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    
    medication_name = models.CharField(max_length=200)
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    
    instructions = models.TextField()
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    
    prescribed_date = models.DateField(default=timezone.now)
    start_date = models.DateField()
    end_date = models.DateField()
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medication_name} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_prescriptions'
        ordering = ['-prescribed_date']

class DentalEmergency(models.Model):
    """Emergency dental cases"""
    EMERGENCY_TYPE = [
        ('severe_pain', 'Severe Toothache'),
        ('trauma', 'Dental Trauma'),
        ('swelling', 'Facial Swelling'),
        ('bleeding', 'Uncontrolled Bleeding'),
        ('broken_tooth', 'Broken/Chipped Tooth'),
        ('lost_filling', 'Lost Filling/Crown'),
        ('orthodontic_emergency', 'Orthodontic Emergency'),
        ('abscess', 'Dental Abscess'),
        ('other', 'Other Emergency'),
    ]

    SEVERITY_LEVEL = [
        ('low', 'Low - Can wait for regular appointment'),
        ('medium', 'Medium - Needs attention within 24 hours'),
        ('high', 'High - Needs immediate attention'),
        ('critical', 'Critical - Life-threatening'),
    ]

    emergency_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergencies')
    attending_dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='emergencies', null=True, blank=True)
    
    emergency_type = models.CharField(max_length=25, choices=EMERGENCY_TYPE)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVEL)
    
    symptoms_description = models.TextField()
    pain_level = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    onset_time = models.DateTimeField()
    
    # Triage Information
    triage_notes = models.TextField(blank=True)
    vital_signs = models.JSONField(default=dict, blank=True)
    allergies_checked = models.BooleanField(default=False)
    
    # Treatment
    immediate_treatment = models.TextField(blank=True)
    medications_given = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=True)
    follow_up_scheduled = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Emergency: {self.get_emergency_type_display()} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_emergencies'
        ordering = ['-created_at']

class TreatmentPlan(models.Model):
    """Comprehensive treatment planning"""
    PLAN_STATUS = [
        ('draft', 'Draft'),
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    plan_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='treatment_plans')
    primary_dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name='treatment_plans')
    
    plan_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Clinical Assessment
    chief_complaint = models.TextField()
    clinical_findings = models.TextField()
    diagnosis = models.TextField()
    prognosis = models.TextField()
    
    # Treatment Phases
    phase_1_treatment = models.TextField(blank=True, help_text="Emergency/Pain relief")
    phase_2_treatment = models.TextField(blank=True, help_text="Disease control")
    phase_3_treatment = models.TextField(blank=True, help_text="Restorative")
    phase_4_treatment = models.TextField(blank=True, help_text="Maintenance")
    
    # Financial Planning
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    insurance_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    patient_portion = models.DecimalField(max_digits=10, decimal_places=2)
    payment_plan = models.TextField(blank=True)
    
    # Timeline
    estimated_duration = models.PositiveIntegerField(help_text="Duration in weeks")
    start_date = models.DateField()
    estimated_completion = models.DateField()
    actual_completion = models.DateField(null=True, blank=True)
    
    # Status and Approval
    status = models.CharField(max_length=15, choices=PLAN_STATUS, default='draft')
    patient_approved = models.BooleanField(default=False)
    patient_approval_date = models.DateTimeField(null=True, blank=True)
    
    # AI Enhancement
    ai_risk_assessment = models.JSONField(default=dict, blank=True)
    ai_treatment_suggestions = models.JSONField(default=list, blank=True)
    ai_outcome_prediction = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Treatment Plan: {self.plan_name} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'dentistry_treatment_plans'
        ordering = ['-created_at']


class DentistryInstitution(models.Model):
    """Dental institution/clinic model for S3 data management"""
    INSTITUTION_TYPES = [
        ('dental_clinic', 'Dental Clinic'),
        ('orthodontic_clinic', 'Orthodontic Clinic'),
        ('oral_surgery_center', 'Oral Surgery Center'),
        ('dental_hospital', 'Dental Hospital'),
        ('pediatric_dental_clinic', 'Pediatric Dental Clinic'),
        ('cosmetic_dental_center', 'Cosmetic Dental Center'),
    ]
    
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=30, choices=INSTITUTION_TYPES, default='dental_clinic')
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    license_number = models.CharField(max_length=50, unique=True)
    specializations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        db_table = 'dentistry_institutions'
        ordering = ['-created_at']


class DentistryPatient(models.Model):
    """Enhanced patient model for S3 data management"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    medical_history = models.TextField(blank=True)
    dental_history = models.TextField(blank=True)
    chief_complaint = models.TextField(blank=True)
    institution = models.ForeignKey(DentistryInstitution, on_delete=models.CASCADE, related_name='patients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        db_table = 'dentistry_s3_patients'
        ordering = ['-created_at']


class DentistryFile(models.Model):
    """File storage model for dental data in S3"""
    FILE_TYPES = [
        ('xrays', 'X-Rays'),
        ('photos', 'Clinical Photos'),
        ('impressions', 'Digital Impressions'),
        ('treatment_plans', 'Treatment Plans'),
        ('reports', 'Reports'),
        ('consent_forms', 'Consent Forms'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='general')
    s3_key = models.CharField(max_length=500, unique=True)
    s3_url = models.URLField(max_length=500)
    size = models.BigIntegerField(default=0)  # File size in bytes
    metadata = models.JSONField(default=dict, blank=True)
    institution = models.ForeignKey(DentistryInstitution, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    patient = models.ForeignKey(DentistryPatient, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_file_type_display()})"
    
    class Meta:
        db_table = 'dentistry_s3_files'
        ordering = ['-created_at']


class DentistryAnalysis(models.Model):
    """AI analysis results for dental files"""
    ANALYSIS_TYPES = [
        ('caries_detection', 'Caries Detection'),
        ('orthodontic_analysis', 'Orthodontic Analysis'),
        ('periodontal_assessment', 'Periodontal Assessment'),
        ('oral_pathology', 'Oral Pathology Detection'),
        ('bite_analysis', 'Bite Analysis'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    file = models.ForeignKey(DentistryFile, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confidence_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    results = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    analyzed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.file.name}"
    
    class Meta:
        db_table = 'dentistry_s3_analyses'
        ordering = ['-created_at']
