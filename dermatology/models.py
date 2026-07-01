from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class DermatologyDepartment(models.Model):
    """Dermatology Department Configuration"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    head_doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='head_dermatology_departments'
    )
    location = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    operating_hours = models.CharField(max_length=200, blank=True)
    emergency_services = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_departments'
        verbose_name = 'Dermatology Department'
        verbose_name_plural = 'Dermatology Departments'

    def __str__(self):
        return self.name


class SkinCondition(models.Model):
    """Skin Conditions/Diagnoses Registry"""
    
    CONDITION_CATEGORIES = [
        ('inflammatory', 'Inflammatory'),
        ('infectious', 'Infectious'),
        ('neoplastic', 'Neoplastic'),
        ('genetic', 'Genetic'),
        ('autoimmune', 'Autoimmune'),
        ('allergic', 'Allergic'),
        ('cosmetic', 'Cosmetic'),
        ('other', 'Other')
    ]
    
    SEVERITY_LEVELS = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    icd10_code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, choices=CONDITION_CATEGORIES)
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField()
    symptoms = models.TextField(blank=True)
    risk_factors = models.TextField(blank=True)
    treatment_guidelines = models.TextField(blank=True)
    is_contagious = models.BooleanField(default=False)
    requires_biopsy = models.BooleanField(default=False)
    typical_duration = models.CharField(max_length=100, blank=True)
    recurrence_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skin_conditions'
        verbose_name = 'Skin Condition'
        verbose_name_plural = 'Skin Conditions'
        unique_together = ['name', 'icd10_code']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Patient(models.Model):
    """Patient Information for Dermatology"""
    
    SKIN_TYPES = [
        ('type_1', 'Type I - Always burns, never tans'),
        ('type_2', 'Type II - Usually burns, tans poorly'),
        ('type_3', 'Type III - Sometimes burns, tans gradually'),
        ('type_4', 'Type IV - Burns minimally, always tans well'),
        ('type_5', 'Type V - Very rarely burns, tans very easily'),
        ('type_6', 'Type VI - Never burns')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='dermatology_patient'
    )
    medical_record_number = models.CharField(max_length=50, unique=True)
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPES, blank=True)
    family_history = models.TextField(blank=True)
    known_allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    sun_exposure_history = models.TextField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    smoking_status = models.BooleanField(default=False)
    alcohol_consumption = models.CharField(max_length=100, blank=True)
    previous_skin_cancer = models.BooleanField(default=False)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_patients'
        verbose_name = 'Dermatology Patient'
        verbose_name_plural = 'Dermatology Patients'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.medical_record_number}"


class DermatologyConsultation(models.Model):
    """Dermatology Consultation/Appointment"""
    
    CONSULTATION_TYPES = [
        ('initial', 'Initial Consultation'),
        ('follow_up', 'Follow-up'),
        ('screening', 'Skin Cancer Screening'),
        ('cosmetic', 'Cosmetic Consultation'),
        ('emergency', 'Emergency'),
        ('second_opinion', 'Second Opinion')
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled')
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergent', 'Emergent')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='dermatology_consultations'
    )
    dermatologist = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='dermatology_consultations'
    )
    department = models.ForeignKey(
        DermatologyDepartment, 
        on_delete=models.CASCADE, 
        related_name='consultations'
    )
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPES)
    scheduled_date = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(blank=True)
    review_of_systems = models.TextField(blank=True)
    physical_examination = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    next_appointment_recommended = models.DateTimeField(null=True, blank=True)
    consultation_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_dermatology_consultations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_consultations'
        verbose_name = 'Dermatology Consultation'
        verbose_name_plural = 'Dermatology Consultations'

    def __str__(self):
        return f"Consultation {self.consultation_number} - {self.patient.user.get_full_name()}"


class DiagnosticProcedure(models.Model):
    """Dermatological Diagnostic Procedures"""
    
    PROCEDURE_TYPES = [
        ('biopsy', 'Skin Biopsy'),
        ('dermoscopy', 'Dermoscopy'),
        ('patch_test', 'Patch Testing'),
        ('wood_lamp', 'Wood\'s Lamp Examination'),
        ('koh_prep', 'KOH Preparation'),
        ('tzanck_smear', 'Tzanck Smear'),
        ('bacterial_culture', 'Bacterial Culture'),
        ('fungal_culture', 'Fungal Culture'),
        ('viral_culture', 'Viral Culture'),
        ('immunofluorescence', 'Direct Immunofluorescence'),
        ('confocal_microscopy', 'Confocal Microscopy'),
        ('optical_coherence_tomography', 'Optical Coherence Tomography'),
        ('phototesting', 'Phototesting'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    procedure_number = models.CharField(max_length=50, unique=True)
    consultation = models.ForeignKey(
        DermatologyConsultation, 
        on_delete=models.CASCADE, 
        related_name='diagnostic_procedures'
    )
    procedure_type = models.CharField(max_length=30, choices=PROCEDURE_TYPES)
    procedure_name = models.CharField(max_length=200)
    indication = models.TextField()
    anatomical_location = models.CharField(max_length=200)
    procedure_date = models.DateTimeField()
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='performed_dermatology_procedures'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    procedure_details = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    post_procedure_care = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_diagnostic_procedures'
        verbose_name = 'Diagnostic Procedure'
        verbose_name_plural = 'Diagnostic Procedures'

    def __str__(self):
        return f"{self.procedure_name} - {self.procedure_number}"


class SkinPhoto(models.Model):
    """Dermatological Photography for Documentation"""
    
    PHOTO_TYPES = [
        ('clinical', 'Clinical Documentation'),
        ('dermoscopy', 'Dermoscopy Image'),
        ('before_treatment', 'Before Treatment'),
        ('after_treatment', 'After Treatment'),
        ('progression', 'Disease Progression'),
        ('wound_care', 'Wound Care Documentation'),
        ('surgical', 'Surgical Documentation'),
        ('teaching', 'Teaching/Educational'),
        ('research', 'Research')
    ]
    
    ANATOMICAL_REGIONS = [
        ('face', 'Face'),
        ('scalp', 'Scalp'),
        ('neck', 'Neck'),
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('abdomen', 'Abdomen'),
        ('arms', 'Arms'),
        ('hands', 'Hands'),
        ('legs', 'Legs'),
        ('feet', 'Feet'),
        ('genitalia', 'Genitalia'),
        ('full_body', 'Full Body'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        DermatologyConsultation, 
        on_delete=models.CASCADE, 
        related_name='skin_photos'
    )
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPES)
    anatomical_region = models.CharField(max_length=20, choices=ANATOMICAL_REGIONS)
    specific_location = models.CharField(max_length=200, blank=True)
    image_file = models.ImageField(upload_to='dermatology/photos/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='dermatology/thumbnails/%Y/%m/%d/', blank=True)
    description = models.TextField(blank=True)
    magnification = models.CharField(max_length=50, blank=True)
    lighting_conditions = models.CharField(max_length=100, blank=True)
    camera_settings = models.JSONField(default=dict, blank=True)
    taken_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='taken_dermatology_photos'
    )
    taken_at = models.DateTimeField(default=timezone.now)
    is_before_treatment = models.BooleanField(default=False)
    is_after_treatment = models.BooleanField(default=False)
    treatment_day = models.IntegerField(null=True, blank=True)
    consent_obtained = models.BooleanField(default=False)
    research_use_permitted = models.BooleanField(default=False)
    teaching_use_permitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_skin_photos'
        verbose_name = 'Skin Photo'
        verbose_name_plural = 'Skin Photos'

    def __str__(self):
        return f"{self.photo_type} - {self.anatomical_region} ({self.taken_at.date()})"


class TreatmentPlan(models.Model):
    """Dermatological Treatment Plans"""
    
    TREATMENT_CATEGORIES = [
        ('topical', 'Topical Therapy'),
        ('systemic', 'Systemic Therapy'),
        ('surgical', 'Surgical Intervention'),
        ('laser', 'Laser Therapy'),
        ('phototherapy', 'Phototherapy'),
        ('cryotherapy', 'Cryotherapy'),
        ('immunotherapy', 'Immunotherapy'),
        ('lifestyle', 'Lifestyle Modifications'),
        ('follow_up', 'Follow-up Care'),
        ('preventive', 'Preventive Measures')
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('modified', 'Modified')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        DermatologyConsultation, 
        on_delete=models.CASCADE, 
        related_name='treatment_plans'
    )
    diagnosed_condition = models.ForeignKey(
        SkinCondition, 
        on_delete=models.CASCADE, 
        related_name='treatment_plans'
    )
    treatment_category = models.CharField(max_length=20, choices=TREATMENT_CATEGORIES)
    treatment_name = models.CharField(max_length=200)
    treatment_description = models.TextField()
    medication_name = models.CharField(max_length=200, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    application_instructions = models.TextField(blank=True)
    precautions = models.TextField(blank=True)
    expected_outcomes = models.TextField(blank=True)
    potential_side_effects = models.TextField(blank=True)
    start_date = models.DateField()
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    effectiveness_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    patient_compliance = models.CharField(max_length=100, blank=True)
    treatment_notes = models.TextField(blank=True)
    prescribed_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='prescribed_dermatology_treatments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_treatment_plans'
        verbose_name = 'Treatment Plan'
        verbose_name_plural = 'Treatment Plans'

    def __str__(self):
        return f"{self.treatment_name} for {self.diagnosed_condition.name}"


class TreatmentOutcome(models.Model):
    """Treatment Outcome Tracking"""
    
    OUTCOME_STATUS = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('no_response', 'No Response'),
        ('adverse_reaction', 'Adverse Reaction')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    treatment_plan = models.ForeignKey(
        TreatmentPlan, 
        on_delete=models.CASCADE, 
        related_name='outcomes'
    )
    assessment_date = models.DateField()
    outcome_status = models.CharField(max_length=20, choices=OUTCOME_STATUS)
    improvement_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    symptom_severity_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    patient_satisfaction = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    side_effects_reported = models.TextField(blank=True)
    quality_of_life_impact = models.TextField(blank=True)
    objective_measurements = models.JSONField(default=dict, blank=True)
    clinical_notes = models.TextField()
    next_assessment_date = models.DateField(null=True, blank=True)
    treatment_modifications = models.TextField(blank=True)
    assessed_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assessed_dermatology_outcomes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_treatment_outcomes'
        verbose_name = 'Treatment Outcome'
        verbose_name_plural = 'Treatment Outcomes'

    def __str__(self):
        return f"Outcome for {self.treatment_plan.treatment_name} - {self.outcome_status}"


class AIAnalysis(models.Model):
    """AI-Powered Skin Analysis Results"""
    
    ANALYSIS_TYPES = [
        ('lesion_detection', 'Lesion Detection'),
        ('cancer_screening', 'Cancer Screening'),
        ('acne_assessment', 'Acne Assessment'),
        ('pigmentation_analysis', 'Pigmentation Analysis'),
        ('wrinkle_analysis', 'Wrinkle Analysis'),
        ('texture_analysis', 'Skin Texture Analysis'),
        ('comparative_analysis', 'Comparative Analysis'),
        ('treatment_prediction', 'Treatment Prediction')
    ]
    
    CONFIDENCE_LEVELS = [
        ('very_low', 'Very Low (0-20%)'),
        ('low', 'Low (21-40%)'),
        ('moderate', 'Moderate (41-60%)'),
        ('high', 'High (61-80%)'),
        ('very_high', 'Very High (81-100%)')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skin_photo = models.ForeignKey(
        SkinPhoto, 
        on_delete=models.CASCADE, 
        related_name='ai_analyses'
    )
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPES)
    ai_model_version = models.CharField(max_length=50)
    analysis_date = models.DateTimeField(auto_now_add=True)
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVELS)
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    primary_findings = models.JSONField(default=dict)
    secondary_findings = models.JSONField(default=dict, blank=True)
    risk_assessment = models.TextField(blank=True)
    recommended_actions = models.TextField(blank=True)
    differential_diagnosis = models.JSONField(default=list, blank=True)
    feature_analysis = models.JSONField(default=dict, blank=True)
    lesion_measurements = models.JSONField(default=dict, blank=True)
    color_analysis = models.JSONField(default=dict, blank=True)
    texture_metrics = models.JSONField(default=dict, blank=True)
    asymmetry_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    border_irregularity = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    color_variation = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    diameter_mm = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    evolution_detected = models.BooleanField(default=False)
    requires_biopsy = models.BooleanField(default=False)
    urgency_level = models.CharField(max_length=20, default='routine')
    validated_by_doctor = models.BooleanField(default=False)
    doctor_agreement = models.BooleanField(null=True, blank=True)
    doctor_notes = models.TextField(blank=True)
    processing_time_seconds = models.DecimalField(
        max_digits=8, 
        decimal_places=3, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dermatology_ai_analyses'
        verbose_name = 'AI Analysis'
        verbose_name_plural = 'AI Analyses'

    def __str__(self):
        return f"AI {self.analysis_type} - {self.confidence_level} confidence"
