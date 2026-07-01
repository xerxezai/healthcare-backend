from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class HomeopathyPatient(models.Model):
    """Extended patient model for S3 data management"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    CONSTITUTION_CHOICES = [
        ('carbonica', 'Calcarea Carbonica'),
        ('phosphorus', 'Phosphorus'),
        ('sulphur', 'Sulphur'),
        ('lycopodium', 'Lycopodium'),
        ('natrum_mur', 'Natrum Muriaticum'),
        ('sepia', 'Sepia'),
        ('pulsatilla', 'Pulsatilla'),
        ('arsenicum', 'Arsenicum Album'),
        ('carbonic', 'Carbonic (Calcium)'),  # keeping backward compatibility
        ('phosphoric', 'Phosphoric (Phosphorus)'),
        ('fluoric', 'Fluoric (Fluorine)'),
        ('sulphuric', 'Sulphuric (Sulphur)'),
        ('natrum', 'Natrum (Sodium)'),
        ('silica', 'Silica'),
        ('iron', 'Iron'),
        ('magnesium', 'Magnesium'),
    ]
    
    MIASMATIC_BACKGROUNDS = [
        ('psoric', 'Psoric'),
        ('sycotic', 'Sycotic'),
        ('syphilitic', 'Syphilitic'),
        ('tubercular', 'Tubercular'),
        ('cancerous', 'Cancerous'),
        ('mixed', 'Mixed Miasma'),
    ]
    
    # Extended fields for S3 management
    patient_id = models.CharField(max_length=50, unique=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Backward compatibility fields
    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    constitution = models.CharField(max_length=20, choices=CONSTITUTION_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # New S3 management fields
    date_of_birth = models.DateField(null=True, blank=True)
    constitution_type = models.CharField(max_length=50, choices=CONSTITUTION_CHOICES, blank=True)
    miasmatic_background = models.CharField(max_length=50, choices=MIASMATIC_BACKGROUNDS, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    medical_record_number = models.CharField(max_length=50, blank=True)
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    referring_practitioner = models.CharField(max_length=200, blank=True)
    medical_history = models.JSONField(default=list, help_text="Medical history entries")
    family_history = models.JSONField(default=list, help_text="Family medical history")
    constitutional_symptoms = models.JSONField(default=list, help_text="Constitutional symptom patterns")
    lifestyle_factors = models.JSONField(default=dict, help_text="Lifestyle and environmental factors")
    institution = models.ForeignKey('HomeopathyInstitution', on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.patient_id or 'No ID'})"
        return f"{self.name} - {self.age}y {self.gender}"
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class HomeopathyRemedy(models.Model):
    """Homeopathic remedy database"""
    MIASM_CHOICES = [
        ('psoric', 'Psoric'),
        ('sycotic', 'Sycotic'),
        ('syphilitic', 'Syphilitic'),
        ('tubercular', 'Tubercular'),
        ('acute', 'Acute'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    latin_name = models.CharField(max_length=150, blank=True)
    common_name = models.CharField(max_length=150, blank=True)
    
    # Key characteristics
    keynotes = models.JSONField(default=list, help_text="List of key symptoms/characteristics")
    mental_symptoms = models.JSONField(default=list, help_text="Mental and emotional symptoms")
    physical_symptoms = models.JSONField(default=list, help_text="Physical symptoms and modalities")
    indications = models.JSONField(default=list, help_text="Main therapeutic indications")
    
    # Constitutional information
    miasm = models.CharField(max_length=20, choices=MIASM_CHOICES)
    constitution_affinity = models.JSONField(default=list, help_text="Constitutional types it suits")
    
    # Prescribing information
    common_potencies = models.CharField(max_length=100, default="6C, 30C, 200C")
    dosage_notes = models.TextField(blank=True)
    
    # Relationships
    antidotes = models.ManyToManyField('self', symmetrical=False, related_name='antidoted_by', blank=True)
    complementary = models.ManyToManyField('self', symmetrical=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class HomeopathyDiagnosis(models.Model):
    """AI-powered diagnosis session"""
    STATUS_CHOICES = [
        ('pending', 'Pending Analysis'),
        ('analyzing', 'AI Analysis in Progress'),
        ('completed', 'Analysis Completed'),
        ('reviewed', 'Reviewed by Practitioner'),
        ('prescribed', 'Remedy Prescribed'),
    ]
    
    # Patient information
    patient = models.ForeignKey(HomeopathyPatient, on_delete=models.CASCADE, related_name='diagnoses')
    practitioner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Chief complaints
    primary_symptoms = models.TextField()
    duration = models.CharField(max_length=100, blank=True)
    onset = models.CharField(max_length=100, blank=True)
    severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=5)
    
    # Mental & Emotional
    mental_state = models.TextField(blank=True)
    emotional_pattern = models.TextField(blank=True)
    fears = models.TextField(blank=True)
    anxieties = models.TextField(blank=True)
    mood = models.CharField(max_length=100, blank=True)
    
    # Physical generals
    appetite = models.CharField(max_length=200, blank=True)
    thirst = models.CharField(max_length=200, blank=True)
    sleep = models.CharField(max_length=200, blank=True)
    dreams = models.CharField(max_length=200, blank=True)
    thermals = models.CharField(max_length=200, blank=True)
    perspiration = models.CharField(max_length=200, blank=True)
    
    # Modalities
    better_by = models.TextField(blank=True, help_text="What makes symptoms better")
    worse_by = models.TextField(blank=True, help_text="What makes symptoms worse")
    time_aggravation = models.CharField(max_length=100, blank=True)
    
    # Constitutional
    energy = models.CharField(max_length=200, blank=True)
    circulation = models.CharField(max_length=200, blank=True)
    digestion = models.CharField(max_length=200, blank=True)
    elimination = models.CharField(max_length=200, blank=True)
    
    # Miasmatic analysis
    miasm = models.CharField(max_length=20, choices=HomeopathyRemedy.MIASM_CHOICES, blank=True)
    family_history = models.TextField(blank=True)
    past_illness = models.TextField(blank=True)
    
    # Additional information
    lifestyle = models.TextField(blank=True)
    environment = models.TextField(blank=True)
    stress_factors = models.TextField(blank=True)
    previous_treatments = models.TextField(blank=True)
    
    # AI Analysis results
    ai_confidence = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    suggested_constitution = models.CharField(max_length=50, blank=True)
    suggested_miasm = models.CharField(max_length=20, blank=True)
    mental_emotional_score = models.IntegerField(default=0)
    physical_score = models.IntegerField(default=0)
    modality_score = models.IntegerField(default=0)
    
    # Treatment recommendations
    estimated_duration = models.CharField(max_length=50, blank=True)
    suggested_potency = models.CharField(max_length=50, blank=True)
    suggested_frequency = models.CharField(max_length=100, blank=True)
    follow_up_recommendations = models.JSONField(default=list)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    analyzed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Diagnosis for {self.patient.name} on {self.created_at.date()}"
    
    class Meta:
        ordering = ['-created_at']

class HomeopathyRemedySuggestion(models.Model):
    """AI-generated remedy suggestions for a diagnosis"""
    diagnosis = models.ForeignKey(HomeopathyDiagnosis, on_delete=models.CASCADE, related_name='remedy_suggestions')
    remedy = models.ForeignKey(HomeopathyRemedy, on_delete=models.CASCADE)
    
    # AI scoring
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    keynote_match_score = models.FloatField(default=0.0)
    mental_match_score = models.FloatField(default=0.0)
    physical_match_score = models.FloatField(default=0.0)
    constitutional_match_score = models.FloatField(default=0.0)
    
    # Suggested prescription
    suggested_potency = models.CharField(max_length=20, default="30C")
    suggested_frequency = models.CharField(max_length=100, default="Once daily")
    duration = models.CharField(max_length=50, default="3-5 days")
    
    # Reasoning
    ai_reasoning = models.TextField(blank=True, help_text="AI explanation for this suggestion")
    matching_symptoms = models.JSONField(default=list, help_text="Symptoms that matched this remedy")
    
    rank = models.PositiveIntegerField(help_text="Rank in the suggestion list (1=top)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.remedy.name} for {self.diagnosis.patient.name} (Rank #{self.rank})"
    
    class Meta:
        ordering = ['rank']
        unique_together = ['diagnosis', 'rank']


# S3 Data Management Models

class HomeopathyInstitution(models.Model):
    """Extended institution model for S3 data management"""
    INSTITUTION_TYPES = [
        ('clinic', 'Homeopathy Clinic'),
        ('hospital', 'Homeopathy Hospital'),
        ('college', 'Homeopathy College'),
        ('research_center', 'Research Center'),
        ('pharmacy', 'Homeopathy Pharmacy'),
        ('manufacturing', 'Remedy Manufacturing'),
        ('dispensary', 'Dispensary'),
        ('wellness_center', 'Wellness Center'),
    ]
    
    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=50, choices=INSTITUTION_TYPES)
    license_number = models.CharField(max_length=100, unique=True)
    accreditation_body = models.CharField(max_length=100, blank=True)
    chief_homeopath = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    website = models.URLField(blank=True)
    operating_hours = models.CharField(max_length=200, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    specializations = models.JSONField(default=list, help_text="Institution specializations")
    equipment_list = models.JSONField(default=list, help_text="Equipment and tools available")
    certification_info = models.JSONField(default=dict, help_text="Certification details")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homeopathy Institution"
        verbose_name_plural = "Homeopathy Institutions"

    def __str__(self):
        return f"{self.name} ({self.institution_type})"


class HomeopathyCase(models.Model):
    """Case management for homeopathy practice"""
    CASE_STATUS = [
        ('active', 'Active'),
        ('follow_up', 'Follow-up'),
        ('improved', 'Improved'),
        ('cured', 'Cured'),
        ('discontinued', 'Discontinued'),
        ('referred', 'Referred'),
    ]
    
    CASE_TYPES = [
        ('acute', 'Acute Case'),
        ('chronic', 'Chronic Case'),
        ('constitutional', 'Constitutional Treatment'),
        ('miasmatic', 'Miasmatic Treatment'),
        ('prophylactic', 'Prophylactic'),
        ('follow_up', 'Follow-up'),
    ]
    
    case_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('HomeopathyPatient', on_delete=models.CASCADE, related_name='cases')
    institution = models.ForeignKey('HomeopathyInstitution', on_delete=models.CASCADE, related_name='cases')
    practitioner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeopathy_cases')
    case_type = models.CharField(max_length=50, choices=CASE_TYPES)
    chief_complaint = models.TextField()
    constitutional_type = models.CharField(max_length=50, blank=True)
    miasmatic_analysis = models.TextField(blank=True)
    remedy_prescribed = models.CharField(max_length=200, blank=True)
    potency = models.CharField(max_length=20, blank=True)
    dosage = models.CharField(max_length=200, blank=True)
    modalities = models.JSONField(default=dict, help_text="Better/worse conditions")
    symptom_totality = models.JSONField(default=list, help_text="Complete symptom picture")
    repertorization_data = models.JSONField(default=dict, help_text="Repertorization analysis")
    follow_up_notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CASE_STATUS, default='active')
    next_appointment = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homeopathy Case"
        verbose_name_plural = "Homeopathy Cases"

    def __str__(self):
        return f"Case {self.case_id} - {self.patient.full_name}"


class HomeopathyFile(models.Model):
    """File management for homeopathy data in S3"""
    FILE_TYPES = [
        ('case_taking', 'Case Taking Records'),
        ('constitutional_analysis', 'Constitutional Analysis'),
        ('remedy_prescriptions', 'Remedy Prescriptions'),
        ('follow_up_notes', 'Follow-up Notes'),
        ('miasmatic_analysis', 'Miasmatic Analysis'),
        ('repertorization', 'Repertorization Charts'),
        ('materia_medica', 'Materia Medica References'),
        ('provings', 'Proving Documentation'),
        ('lab_reports', 'Laboratory Reports'),
        ('lifestyle_assessment', 'Lifestyle Assessment'),
    ]
    
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, choices=FILE_TYPES)
    s3_key = models.CharField(max_length=500, unique=True)
    s3_url = models.URLField(max_length=1000)
    institution = models.ForeignKey('HomeopathyInstitution', on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    patient = models.ForeignKey('HomeopathyPatient', on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    case = models.ForeignKey('HomeopathyCase', on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    size = models.BigIntegerField(default=0, help_text="File size in bytes")
    content_type = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, help_text="Additional file metadata")
    description = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_homeopathy_files', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homeopathy File"
        verbose_name_plural = "Homeopathy Files"

    def __str__(self):
        return f"{self.name} ({self.file_type})"


class HomeopathyAnalysis(models.Model):
    """AI/ML analysis results for homeopathy files"""
    ANALYSIS_TYPES = [
        ('constitutional_matching', 'Constitutional Type Matching'),
        ('remedy_selection', 'Remedy Selection Assistant'),
        ('symptom_analysis', 'Symptom Pattern Analysis'),
        ('miasmatic_assessment', 'Miasmatic Background Assessment'),
        ('potency_suggestion', 'Potency Selection Guide'),
        ('repertorization_aid', 'Digital Repertorization'),
    ]
    
    ANALYSIS_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    file = models.ForeignKey('HomeopathyFile', on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS, default='pending')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Analysis confidence score (0-1)")
    results = models.JSONField(default=dict, help_text="Detailed analysis results")
    processing_time = models.DurationField(null=True, blank=True)
    algorithm_version = models.CharField(max_length=50, blank=True)
    parameters_used = models.JSONField(default=dict, help_text="Analysis parameters")
    error_message = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_homeopathy_analyses')
    review_notes = models.TextField(blank=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homeopathy Analysis"
        verbose_name_plural = "Homeopathy Analyses"

    def __str__(self):
        return f"{self.analysis_type} - {self.file.name} ({self.status})"
