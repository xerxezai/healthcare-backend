from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class Patient(models.Model):
    """Extended patient model for general medicine"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicine_patient')
    patient_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=15)
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    social_history = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def bmi(self):
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        return None

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.patient_id}"

    class Meta:
        db_table = 'medicine_patients'

class Doctor(models.Model):
    """Doctor profile model for medicine department"""
    SPECIALIZATION_CHOICES = [
        ('general', 'General Medicine'),
        ('emergency', 'Emergency Medicine'),
        ('internal', 'Internal Medicine'),
        ('family', 'Family Medicine'),
        ('cardiology', 'Cardiology'),
        ('pulmonology', 'Pulmonology'),
        ('gastroenterology', 'Gastroenterology'),
        ('nephrology', 'Nephrology'),
        ('endocrinology', 'Endocrinology'),
        ('rheumatology', 'Rheumatology'),
        ('hematology', 'Hematology'),
        ('oncology', 'Oncology'),
        ('neurology', 'Neurology'),
        ('psychiatry', 'Psychiatry'),
        ('geriatrics', 'Geriatrics'),
        ('intensive_care', 'Intensive Care Medicine'),
    ]

    QUALIFICATION_CHOICES = [
        ('MBBS', 'MBBS'),
        ('MD', 'MD'),
        ('DO', 'DO'),
        ('DNB', 'DNB'),
        ('DM', 'DM'),
        ('MCh', 'MCh'),
        ('FRCP', 'FRCP'),
        ('FACS', 'FACS'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, default='general')
    qualification = models.CharField(max_length=10, choices=QUALIFICATION_CHOICES, default='MBBS')
    years_experience = models.PositiveIntegerField(default=0)
    education = models.TextField()
    certifications = models.TextField(blank=True)
    hospital_affiliation = models.CharField(max_length=200, blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    available_hours = models.JSONField(default=dict, help_text="Availability schedule")
    is_available_emergency = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='doctor_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"

    class Meta:
        db_table = 'medicine_doctors'

class VitalSigns(models.Model):
    """Patient vital signs recording"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature in Celsius")
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Beats per minute")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Breaths per minute")
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True, help_text="SpO2 percentage", validators=[MinValueValidator(0), MaxValueValidator(100)])
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    bmi = models.FloatField(null=True, blank=True, editable=False)
    pain_scale = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.weight and self.height:
            height_m = self.height / 100
            self.bmi = round(self.weight / (height_m ** 2), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.patient_id} - Vitals on {self.recorded_at.date()}"

    class Meta:
        db_table = 'medicine_vital_signs'
        ordering = ['-recorded_at']

class Appointment(models.Model):
    """Appointment scheduling for medicine department"""
    APPOINTMENT_TYPE_CHOICES = [
        ('consultation', 'General Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('routine_checkup', 'Routine Checkup'),
        ('preventive_care', 'Preventive Care'),
        ('chronic_care', 'Chronic Care Management'),
        ('second_opinion', 'Second Opinion'),
        ('telemedicine', 'Telemedicine'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]

    appointment_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='consultation')
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    chief_complaint = models.TextField()
    notes = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    prescription_given = models.BooleanField(default=False)
    lab_tests_ordered = models.BooleanField(default=False)
    referral_given = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            self.appointment_id = f"APT{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()}"

    class Meta:
        db_table = 'medicine_appointments'
        ordering = ['-scheduled_datetime']

class Prescription(models.Model):
    """Prescription management"""
    MEDICATION_TYPE_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('ointment', 'Ointment'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('suppository', 'Suppository'),
        ('patch', 'Patch'),
    ]

    FREQUENCY_CHOICES = [
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times', 'Three Times Daily'),
        ('four_times', 'Four Times Daily'),
        ('as_needed', 'As Needed'),
        ('before_meals', 'Before Meals'),
        ('after_meals', 'After Meals'),
        ('at_bedtime', 'At Bedtime'),
        ('every_other_day', 'Every Other Day'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    prescription_id = models.CharField(max_length=20, unique=True, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=200)
    medication_type = models.CharField(max_length=15, choices=MEDICATION_TYPE_CHOICES, default='tablet')
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='twice_daily')
    duration_days = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    instructions = models.TextField()
    warnings = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    is_generic_allowed = models.BooleanField(default=True)
    refills_allowed = models.PositiveIntegerField(default=0)
    dispensed = models.BooleanField(default=False)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.prescription_id:
            self.prescription_id = f"RX{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prescription_id} - {self.medication_name} for {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'medicine_prescriptions'
        ordering = ['-created_at']

class LabTest(models.Model):
    """Laboratory test orders and results"""
    TEST_CATEGORY_CHOICES = [
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('stool', 'Stool Test'),
        ('microbiology', 'Microbiology'),
        ('biochemistry', 'Biochemistry'),
        ('hematology', 'Hematology'),
        ('immunology', 'Immunology'),
        ('molecular', 'Molecular Biology'),
        ('genetic', 'Genetic Testing'),
        ('toxicology', 'Toxicology'),
    ]

    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('sample_collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    test_id = models.CharField(max_length=20, unique=True, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='lab_tests')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_tests')
    ordered_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_tests')
    test_name = models.CharField(max_length=200)
    test_category = models.CharField(max_length=15, choices=TEST_CATEGORY_CHOICES, default='blood')
    test_code = models.CharField(max_length=20, blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    ordered_date = models.DateTimeField(auto_now_add=True)
    sample_collected_date = models.DateTimeField(null=True, blank=True)
    result_date = models.DateTimeField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True, help_text="Test results in JSON format")
    result_interpretation = models.TextField(blank=True)
    reference_range = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    lab_comments = models.TextField(blank=True)
    report_file = models.FileField(upload_to='lab_reports/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.test_id:
            self.test_id = f"LAB{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.test_id} - {self.test_name} for {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'medicine_lab_tests'
        ordering = ['-ordered_date']

class EmergencyCase(models.Model):
    """Emergency medicine case management"""
    TRIAGE_LEVEL_CHOICES = [
        ('1', 'Level 1 - Immediate (Life-threatening)'),
        ('2', 'Level 2 - Emergent (High risk)'),
        ('3', 'Level 3 - Urgent (Moderate risk)'),
        ('4', 'Level 4 - Less Urgent (Low risk)'),
        ('5', 'Level 5 - Non-urgent (No risk)'),
    ]

    ARRIVAL_MODE_CHOICES = [
        ('ambulance', 'Ambulance'),
        ('walk_in', 'Walk-in'),
        ('private_vehicle', 'Private Vehicle'),
        ('helicopter', 'Helicopter'),
        ('police', 'Police Transport'),
        ('transfer', 'Hospital Transfer'),
    ]

    DISPOSITION_CHOICES = [
        ('admitted', 'Admitted to Hospital'),
        ('discharged', 'Discharged Home'),
        ('transferred', 'Transferred to Another Facility'),
        ('observation', 'Under Observation'),
        ('ama', 'Against Medical Advice'),
        ('deceased', 'Deceased'),
        ('eloped', 'Left Without Being Seen'),
    ]

    case_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_cases')
    attending_physician = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='emergency_cases')
    triage_nurse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='triaged_cases')
    arrival_datetime = models.DateTimeField(auto_now_add=True)
    arrival_mode = models.CharField(max_length=20, choices=ARRIVAL_MODE_CHOICES, default='walk_in')
    triage_level = models.CharField(max_length=1, choices=TRIAGE_LEVEL_CHOICES, default='3')
    chief_complaint = models.TextField()
    history_present_illness = models.TextField()
    vital_signs_on_arrival = models.JSONField(default=dict)
    physical_examination = models.TextField()
    pain_assessment = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    primary_diagnosis = models.TextField()
    secondary_diagnoses = models.TextField(blank=True)
    procedures_performed = models.TextField(blank=True)
    medications_given = models.TextField(blank=True)
    imaging_ordered = models.TextField(blank=True)
    lab_work_ordered = models.TextField(blank=True)
    consultations_requested = models.TextField(blank=True)
    treatment_summary = models.TextField()
    disposition = models.CharField(max_length=15, choices=DISPOSITION_CHOICES, default='discharged')
    discharge_instructions = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    time_to_provider = models.DurationField(null=True, blank=True, help_text="Time from arrival to seeing provider")
    total_ed_time = models.DurationField(null=True, blank=True, help_text="Total time in emergency department")
    is_trauma = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    requires_admission = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.case_id:
            self.case_id = f"EM{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_id} - {self.patient.user.get_full_name()} - Triage {self.triage_level}"

    class Meta:
        db_table = 'medicine_emergency_cases'
        ordering = ['-arrival_datetime']

class TreatmentPlan(models.Model):
    """Comprehensive treatment plan management"""
    PLAN_TYPE_CHOICES = [
        ('acute', 'Acute Care'),
        ('chronic', 'Chronic Care Management'),
        ('preventive', 'Preventive Care'),
        ('palliative', 'Palliative Care'),
        ('rehabilitation', 'Rehabilitation'),
        ('emergency', 'Emergency Treatment'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('discontinued', 'Discontinued'),
        ('modified', 'Modified'),
    ]

    plan_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='treatment_plans')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='created_treatment_plans')
    plan_type = models.CharField(max_length=15, choices=PLAN_TYPE_CHOICES, default='acute')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    primary_diagnosis = models.TextField()
    secondary_diagnoses = models.TextField(blank=True)
    treatment_goals = models.TextField()
    interventions = models.TextField()
    medications = models.TextField()
    therapies = models.TextField(blank=True)
    lifestyle_modifications = models.TextField(blank=True)
    monitoring_parameters = models.TextField()
    follow_up_schedule = models.TextField()
    expected_outcomes = models.TextField()
    potential_complications = models.TextField(blank=True)
    emergency_contact_instructions = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.plan_id:
            self.plan_id = f"TP{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plan_id} - {self.patient.user.get_full_name()} - {self.get_plan_type_display()}"

    class Meta:
        db_table = 'medicine_treatment_plans'
        ordering = ['-created_at']

class MedicalRecord(models.Model):
    """Comprehensive medical record management"""
    RECORD_TYPE_CHOICES = [
        ('consultation', 'Consultation Note'),
        ('progress', 'Progress Note'),
        ('discharge', 'Discharge Summary'),
        ('procedure', 'Procedure Note'),
        ('operation', 'Operation Note'),
        ('emergency', 'Emergency Note'),
        ('transfer', 'Transfer Note'),
    ]

    record_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, related_name='medical_records')
    emergency_case = models.ForeignKey(EmergencyCase, on_delete=models.CASCADE, null=True, blank=True, related_name='medical_records')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='created_medical_records')
    record_type = models.CharField(max_length=15, choices=RECORD_TYPE_CHOICES, default='consultation')
    subject = models.CharField(max_length=200)
    subjective = models.TextField(help_text="Patient's symptoms and history")
    objective = models.TextField(help_text="Physical examination findings")
    assessment = models.TextField(help_text="Diagnosis and clinical impression")
    plan = models.TextField(help_text="Treatment plan and recommendations")
    vital_signs = models.JSONField(null=True, blank=True)
    medications_prescribed = models.TextField(blank=True)
    procedures_performed = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    imaging_results = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    provider_signature = models.CharField(max_length=100)
    is_dictated = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list, help_text="List of attached files")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.record_id:
            self.record_id = f"MR{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.record_id} - {self.patient.user.get_full_name()} - {self.get_record_type_display()}"

    class Meta:
        db_table = 'medicine_medical_records'
        ordering = ['-created_at']

class PatientReport(models.Model):
    """Patient reports and documentation"""
    REPORT_TYPE_CHOICES = [
        ('medical_summary', 'Medical Summary Report'),
        ('discharge_summary', 'Discharge Summary'),
        ('lab_summary', 'Laboratory Summary'),
        ('imaging_summary', 'Imaging Summary'),
        ('medication_history', 'Medication History'),
        ('progress_report', 'Progress Report'),
        ('referral_report', 'Referral Report'),
        ('insurance_report', 'Insurance Report'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('archived', 'Archived'),
    ]

    report_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_reports')
    generated_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='generated_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='medical_summary')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=200)
    content = models.TextField()
    data_range_start = models.DateField(null=True, blank=True)
    data_range_end = models.DateField(null=True, blank=True)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_email = models.EmailField(blank=True)
    recipient_organization = models.CharField(max_length=200, blank=True)
    ai_generated_summary = models.TextField(blank=True)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = f"RPT{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_id} - {self.title}"

    class Meta:
        db_table = 'medicine_patient_reports'
        ordering = ['-created_at']

class SOAPNote(models.Model):
    """SOAP Notes Generator"""
    note_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='soap_notes')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, related_name='soap_notes')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='created_soap_notes')
    
    # SOAP Components
    subjective = models.TextField(help_text="Patient's symptoms, concerns, and history")
    objective = models.TextField(help_text="Observable findings, vital signs, physical exam")
    assessment = models.TextField(help_text="Diagnosis, clinical impression, differential diagnosis")
    plan = models.TextField(help_text="Treatment plan, medications, follow-up")
    
    # Additional Components
    chief_complaint = models.TextField()
    history_present_illness = models.TextField()
    review_of_systems = models.TextField(blank=True)
    past_medical_history = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    social_history = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    physical_examination = models.TextField()
    vital_signs_data = models.JSONField(default=dict)
    lab_results = models.TextField(blank=True)
    imaging_results = models.TextField(blank=True)
    
    # AI Enhancement
    ai_suggestions = models.TextField(blank=True)
    ai_differential_diagnosis = models.TextField(blank=True)
    ai_risk_assessment = models.TextField(blank=True)
    
    # Template and Formatting
    template_used = models.CharField(max_length=100, blank=True)
    is_template = models.BooleanField(default=False)
    template_name = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.note_id:
            self.note_id = f"SOAP{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.note_id} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'medicine_soap_notes'
        ordering = ['-created_at']

class ProtocolSummarizer(models.Model):
    """Protocol and guideline summarizer"""
    PROTOCOL_TYPE_CHOICES = [
        ('treatment', 'Treatment Protocol'),
        ('diagnostic', 'Diagnostic Protocol'),
        ('emergency', 'Emergency Protocol'),
        ('surgical', 'Surgical Protocol'),
        ('medication', 'Medication Protocol'),
        ('infection_control', 'Infection Control'),
        ('safety', 'Safety Protocol'),
        ('clinical_guideline', 'Clinical Guideline'),
    ]

    protocol_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=300)
    protocol_type = models.CharField(max_length=20, choices=PROTOCOL_TYPE_CHOICES, default='treatment')
    medical_condition = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100)
    original_document = models.FileField(upload_to='protocols/', null=True, blank=True)
    source_organization = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Summary Components
    executive_summary = models.TextField()
    key_recommendations = models.TextField()
    contraindications = models.TextField(blank=True)
    warnings_precautions = models.TextField(blank=True)
    step_by_step_procedure = models.TextField()
    monitoring_requirements = models.TextField(blank=True)
    expected_outcomes = models.TextField(blank=True)
    complications_management = models.TextField(blank=True)
    
    # AI Generated Content
    ai_summary = models.TextField(blank=True)
    ai_key_points = models.TextField(blank=True)
    ai_risk_factors = models.TextField(blank=True)
    
    tags = models.JSONField(default=list, help_text="Search tags")
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    downloads_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.protocol_id:
            self.protocol_id = f"PROT{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.protocol_id} - {self.title}"

    class Meta:
        db_table = 'medicine_protocol_summarizer'
        ordering = ['-created_at']

class ContractRedlining(models.Model):
    """Contract redlining and review system"""
    CONTRACT_TYPE_CHOICES = [
        ('employment', 'Employment Contract'),
        ('vendor', 'Vendor Agreement'),
        ('insurance', 'Insurance Contract'),
        ('partnership', 'Partnership Agreement'),
        ('equipment_lease', 'Equipment Lease'),
        ('service_agreement', 'Service Agreement'),
        ('consulting', 'Consulting Agreement'),
        ('research', 'Research Agreement'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('redlined', 'Redlined'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('executed', 'Executed'),
    ]

    contract_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=300)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='service_agreement')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    
    # Contract Details
    counterparty_name = models.CharField(max_length=200)
    contract_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Documents
    original_document = models.FileField(upload_to='contracts/original/')
    redlined_document = models.FileField(upload_to='contracts/redlined/', null=True, blank=True)
    final_document = models.FileField(upload_to='contracts/final/', null=True, blank=True)
    
    # Review and Redlining
    review_notes = models.TextField(blank=True)
    redline_comments = models.JSONField(default=list, help_text="List of redline comments")
    risk_assessment = models.TextField(blank=True)
    key_terms_summary = models.TextField(blank=True)
    
    # AI Analysis
    ai_risk_analysis = models.TextField(blank=True)
    ai_suggested_changes = models.TextField(blank=True)
    ai_compliance_check = models.TextField(blank=True)
    
    # Workflow
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contracts')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_contracts')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contracts')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_contracts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.contract_id:
            self.contract_id = f"CTR{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contract_id} - {self.title}"

    class Meta:
        db_table = 'medicine_contract_redlining'
        ordering = ['-created_at']

class PhysicianAssistant(models.Model):
    """AI Physician Assistant for clinical decision support"""
    SESSION_TYPE_CHOICES = [
        ('diagnosis_support', 'Diagnosis Support'),
        ('treatment_planning', 'Treatment Planning'),
        ('drug_interaction', 'Drug Interaction Check'),
        ('clinical_guidelines', 'Clinical Guidelines'),
        ('differential_diagnosis', 'Differential Diagnosis'),
        ('risk_assessment', 'Risk Assessment'),
        ('symptom_analysis', 'Symptom Analysis'),
        ('case_consultation', 'Case Consultation'),
    ]

    session_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_consultations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ai_consultations')
    session_type = models.CharField(max_length=25, choices=SESSION_TYPE_CHOICES, default='diagnosis_support')
    
    # Input Data
    chief_complaint = models.TextField()
    symptoms = models.TextField()
    vital_signs = models.JSONField(default=dict)
    lab_results = models.TextField(blank=True)
    imaging_results = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    
    # AI Analysis
    ai_analysis = models.TextField()
    suggested_diagnoses = models.JSONField(default=list)
    confidence_scores = models.JSONField(default=dict)
    recommended_tests = models.TextField(blank=True)
    treatment_suggestions = models.TextField(blank=True)
    drug_interactions = models.TextField(blank=True)
    risk_factors = models.TextField(blank=True)
    red_flags = models.TextField(blank=True)
    
    # Decision Support
    clinical_guidelines_referenced = models.TextField(blank=True)
    evidence_level = models.CharField(max_length=50, blank=True)
    follow_up_recommendations = models.TextField(blank=True)
    
    # User Interaction
    user_feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    was_helpful = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = f"PA{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session_id} - {self.get_session_type_display()}"

    class Meta:
        db_table = 'medicine_physician_assistant'
        ordering = ['-created_at']

class AIBookingAssistant(models.Model):
    """AI Booking Assistant for patient appointments"""
    BOOKING_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('information_gathering', 'Gathering Information'),
        ('slot_selection', 'Slot Selection'),
        ('confirmation_pending', 'Confirmation Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
    ]

    COMMUNICATION_CHANNEL_CHOICES = [
        ('web_chat', 'Web Chat'),
        ('phone_call', 'Phone Call'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('mobile_app', 'Mobile App'),
        ('voice_assistant', 'Voice Assistant'),
    ]

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_bookings')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_booking_sessions')
    
    # Session Details
    status = models.CharField(max_length=25, choices=BOOKING_STATUS_CHOICES, default='initiated')
    communication_channel = models.CharField(max_length=15, choices=COMMUNICATION_CHANNEL_CHOICES, default='web_chat')
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    
    # Patient Preferences
    preferred_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_specialization = models.CharField(max_length=50, blank=True)
    preferred_date_range_start = models.DateField(null=True, blank=True)
    preferred_date_range_end = models.DateField(null=True, blank=True)
    preferred_time_slots = models.JSONField(default=list)
    urgency_level = models.CharField(max_length=20, blank=True)
    
    # Conversation Log
    conversation_log = models.JSONField(default=list, help_text="Chat history with AI assistant")
    patient_requirements = models.TextField(blank=True)
    symptoms_mentioned = models.TextField(blank=True)
    insurance_verification = models.BooleanField(default=False)
    
    # AI Analysis
    intent_analysis = models.TextField(blank=True)
    recommended_specialty = models.CharField(max_length=100, blank=True)
    urgency_assessment = models.TextField(blank=True)
    suggested_appointment_types = models.JSONField(default=list)
    
    # Booking Outcome
    selected_slot = models.DateTimeField(null=True, blank=True)
    booking_confirmation_code = models.CharField(max_length=20, blank=True)
    reminder_preferences = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"AIB{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} - {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'medicine_ai_booking_assistant'
        ordering = ['-created_at']

class InsurancePolicyCopilot(models.Model):
    """Insurance policy copilot for coverage analysis"""
    POLICY_TYPE_CHOICES = [
        ('health_insurance', 'Health Insurance'),
        ('dental_insurance', 'Dental Insurance'),
        ('vision_insurance', 'Vision Insurance'),
        ('disability_insurance', 'Disability Insurance'),
        ('life_insurance', 'Life Insurance'),
        ('workers_comp', 'Workers Compensation'),
        ('malpractice', 'Malpractice Insurance'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]

    policy_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_policies')
    
    # Policy Details
    insurance_provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES, default='health_insurance')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    # Coverage Details
    coverage_start_date = models.DateField()
    coverage_end_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deductible_amount = models.DecimalField(max_digits=10, decimal_places=2)
    copay_amount = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    coinsurance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    out_of_pocket_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Coverage Analysis
    covered_services = models.JSONField(default=list)
    excluded_services = models.JSONField(default=list)
    prior_authorization_required = models.JSONField(default=list)
    network_providers = models.JSONField(default=list)
    
    # AI Analysis
    ai_coverage_summary = models.TextField(blank=True)
    ai_cost_estimation = models.TextField(blank=True)
    ai_recommendations = models.TextField(blank=True)
    ai_risk_assessment = models.TextField(blank=True)
    
    # Claims History
    claims_ytd = models.PositiveIntegerField(default=0)
    claims_paid_ytd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_deductible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.policy_id:
            self.policy_id = f"INS{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.policy_id} - {self.insurance_provider}"

    class Meta:
        db_table = 'medicine_insurance_policy_copilot'
        ordering = ['-created_at']

class HospitalCSRAssistant(models.Model):
    """Hospital Customer Service Representative AI Assistant"""
    INQUIRY_TYPE_CHOICES = [
        ('appointment_scheduling', 'Appointment Scheduling'),
        ('billing_inquiry', 'Billing Inquiry'),
        ('insurance_verification', 'Insurance Verification'),
        ('medical_records', 'Medical Records Request'),
        ('general_information', 'General Information'),
        ('complaint_resolution', 'Complaint Resolution'),
        ('prescription_refill', 'Prescription Refill'),
        ('test_results', 'Test Results Inquiry'),
        ('facility_directions', 'Facility Directions'),
        ('emergency_guidance', 'Emergency Guidance'),
    ]

    RESOLUTION_STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name='csr_tickets')
    
    # Inquiry Details
    inquiry_type = models.CharField(max_length=25, choices=INQUIRY_TYPE_CHOICES, default='general_information')
    subject = models.CharField(max_length=300)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    resolution_status = models.CharField(max_length=15, choices=RESOLUTION_STATUS_CHOICES, default='open')
    
    # Contact Information
    caller_name = models.CharField(max_length=200)
    caller_phone = models.CharField(max_length=20)
    caller_email = models.EmailField(blank=True)
    preferred_contact_method = models.CharField(max_length=50, blank=True)
    
    # AI Assistant Interaction
    conversation_transcript = models.JSONField(default=list)
    ai_analysis = models.TextField(blank=True)
    ai_suggested_responses = models.JSONField(default=list)
    ai_resolution_recommendations = models.TextField(blank=True)
    sentiment_analysis = models.CharField(max_length=50, blank=True)
    
    # Resolution Details
    resolution_summary = models.TextField(blank=True)
    actions_taken = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    # Workflow
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_csr_tickets')
    escalated_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_csr_tickets')
    
    # Metrics
    response_time = models.DurationField(null=True, blank=True)
    resolution_time = models.DurationField(null=True, blank=True)
    customer_satisfaction_rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = f"CSR{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"

    class Meta:
        db_table = 'medicine_hospital_csr_assistant'
        ordering = ['-created_at']

class MedicalResearchReview(models.Model):
    """Medical Research Review Assistant"""
    RESEARCH_TYPE_CHOICES = [
        ('clinical_trial', 'Clinical Trial'),
        ('systematic_review', 'Systematic Review'),
        ('meta_analysis', 'Meta-Analysis'),
        ('case_study', 'Case Study'),
        ('cohort_study', 'Cohort Study'),
        ('randomized_trial', 'Randomized Controlled Trial'),
        ('observational', 'Observational Study'),
        ('literature_review', 'Literature Review'),
    ]

    QUALITY_RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('very_poor', 'Very Poor'),
    ]

    EVIDENCE_LEVEL_CHOICES = [
        ('level_1', 'Level 1 - Systematic Review/Meta-analysis'),
        ('level_2', 'Level 2 - Randomized Controlled Trial'),
        ('level_3', 'Level 3 - Controlled Trial (non-randomized)'),
        ('level_4', 'Level 4 - Case-control/Cohort Study'),
        ('level_5', 'Level 5 - Case Series/Case Report'),
        ('level_6', 'Level 6 - Expert Opinion'),
    ]

    review_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=500)
    authors = models.TextField()
    journal = models.CharField(max_length=300)
    publication_date = models.DateField()
    doi = models.CharField(max_length=200, blank=True)
    pmid = models.CharField(max_length=50, blank=True)
    
    # Research Details
    research_type = models.CharField(max_length=20, choices=RESEARCH_TYPE_CHOICES, default='clinical_trial')
    research_question = models.TextField()
    methodology = models.TextField()
    sample_size = models.PositiveIntegerField(null=True, blank=True)
    study_duration = models.CharField(max_length=100, blank=True)
    
    # Abstract and Content
    abstract = models.TextField()
    key_findings = models.TextField()
    conclusions = models.TextField()
    limitations = models.TextField(blank=True)
    
    # AI Analysis
    ai_summary = models.TextField(blank=True)
    ai_critical_analysis = models.TextField(blank=True)
    ai_clinical_relevance = models.TextField(blank=True)
    ai_methodology_assessment = models.TextField(blank=True)
    ai_bias_assessment = models.TextField(blank=True)
    
    # Quality Assessment
    evidence_level = models.CharField(max_length=10, choices=EVIDENCE_LEVEL_CHOICES, blank=True)
    quality_rating = models.CharField(max_length=15, choices=QUALITY_RATING_CHOICES, blank=True)
    risk_of_bias = models.TextField(blank=True)
    statistical_significance = models.BooleanField(null=True, blank=True)
    clinical_significance = models.TextField(blank=True)
    
    # Categorization
    medical_specialty = models.CharField(max_length=100)
    keywords = models.JSONField(default=list)
    mesh_terms = models.JSONField(default=list)
    
    # Review Metrics
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review_date = models.DateTimeField(auto_now_add=True)
    is_recommended = models.BooleanField(default=False)
    recommendation_notes = models.TextField(blank=True)
    
    # Usage Tracking
    views_count = models.PositiveIntegerField(default=0)
    citations_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.review_id:
            self.review_id = f"RES{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.review_id} - {self.title[:100]}"

    class Meta:
        db_table = 'medicine_medical_research_review'
        ordering = ['-publication_date']

class BackOfficeAutomation(models.Model):
    """Back Office Automation for administrative tasks"""
    TASK_TYPE_CHOICES = [
        ('billing_processing', 'Billing Processing'),
        ('insurance_claims', 'Insurance Claims Processing'),
        ('appointment_reminders', 'Appointment Reminders'),
        ('lab_result_distribution', 'Lab Result Distribution'),
        ('prescription_renewals', 'Prescription Renewals'),
        ('patient_follow_up', 'Patient Follow-up'),
        ('inventory_management', 'Inventory Management'),
        ('compliance_reporting', 'Compliance Reporting'),
        ('quality_metrics', 'Quality Metrics Collection'),
        ('revenue_cycle', 'Revenue Cycle Management'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    FREQUENCY_CHOICES = [
        ('once', 'One-time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('custom', 'Custom Schedule'),
    ]

    automation_id = models.CharField(max_length=20, unique=True, editable=False)
    task_name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=25, choices=TASK_TYPE_CHOICES, default='billing_processing')
    description = models.TextField()
    
    # Scheduling
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='daily')
    schedule_time = models.TimeField(null=True, blank=True)
    custom_schedule = models.CharField(max_length=100, blank=True, help_text="Cron expression for custom scheduling")
    
    # Configuration
    task_parameters = models.JSONField(default=dict, help_text="Task-specific configuration parameters")
    notification_settings = models.JSONField(default=dict)
    error_handling_config = models.JSONField(default=dict)
    
    # Status and Execution
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    execution_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    
    # Execution Log
    execution_log = models.JSONField(default=list, help_text="Recent execution history")
    last_execution_summary = models.TextField(blank=True)
    average_execution_time = models.DurationField(null=True, blank=True)
    
    # AI Enhancement
    ai_optimization_suggestions = models.TextField(blank=True)
    ai_performance_analysis = models.TextField(blank=True)
    
    # Management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_automations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.automation_id:
            self.automation_id = f"AUTO{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.automation_id} - {self.task_name}"

    class Meta:
        db_table = 'medicine_back_office_automation'
        ordering = ['-created_at']

class ClinicalHistorySearch(models.Model):
    """Clinical History Search Engine"""
    SEARCH_TYPE_CHOICES = [
        ('patient_history', 'Patient History Search'),
        ('diagnosis_lookup', 'Diagnosis Lookup'),
        ('medication_history', 'Medication History'),
        ('procedure_history', 'Procedure History'),
        ('lab_results_search', 'Lab Results Search'),
        ('imaging_search', 'Imaging Search'),
        ('symptom_search', 'Symptom-based Search'),
        ('clinical_notes', 'Clinical Notes Search'),
    ]

    search_id = models.CharField(max_length=20, unique=True, editable=False)
    searched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clinical_searches')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name='search_history')
    
    # Search Details
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPE_CHOICES, default='patient_history')
    search_query = models.TextField()
    search_filters = models.JSONField(default=dict, help_text="Applied filters like date range, department, etc.")
    
    # Search Configuration
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    departments_searched = models.JSONField(default=list)
    record_types_searched = models.JSONField(default=list)
    
    # Results
    results_count = models.PositiveIntegerField(default=0)
    search_results = models.JSONField(default=list, help_text="Search results with relevance scores")
    relevant_records = models.JSONField(default=list, help_text="IDs of relevant medical records")
    
    # AI Enhancement
    ai_query_understanding = models.TextField(blank=True)
    ai_suggested_refinements = models.JSONField(default=list)
    ai_related_searches = models.JSONField(default=list)
    semantic_matches = models.JSONField(default=list)
    
    # Performance Metrics
    search_time_ms = models.PositiveIntegerField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    user_satisfaction = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Usage Analytics
    results_clicked = models.JSONField(default=list)
    time_spent_on_results = models.DurationField(null=True, blank=True)
    follow_up_searches = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.search_id:
            self.search_id = f"SRCH{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.search_id} - {self.search_query[:100]}"

    class Meta:
        db_table = 'medicine_clinical_history_search'
        ordering = ['-created_at']


# ============================================================================
# DIABETES MANAGEMENT MODELS
# ============================================================================

class DiabetesPatient(models.Model):
    """Extended diabetes-specific patient information"""
    DIABETES_TYPE_CHOICES = [
        ('type1', 'Type 1 Diabetes'),
        ('type2', 'Type 2 Diabetes'),
        ('gestational', 'Gestational Diabetes'),
        ('prediabetes', 'Pre-diabetes'),
        ('mody', 'MODY (Maturity-Onset Diabetes of the Young)'),
        ('secondary', 'Secondary Diabetes'),
    ]
    
    INSULIN_REGIMEN_CHOICES = [
        ('basal_bolus', 'Basal-Bolus'),
        ('split_mixed', 'Split Mixed'),
        ('pump', 'Insulin Pump'),
        ('none', 'No Insulin'),
    ]
    
    MONITORING_METHOD_CHOICES = [
        ('bgm', 'Blood Glucose Meter'),
        ('cgm', 'Continuous Glucose Monitor'),
        ('flash', 'Flash Glucose Monitor'),
        ('hybrid', 'Hybrid Monitoring'),
    ]

    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='diabetes_profile')
    diabetes_type = models.CharField(max_length=20, choices=DIABETES_TYPE_CHOICES)
    diagnosis_date = models.DateField()
    hba1c_target = models.FloatField(validators=[MinValueValidator(4.0), MaxValueValidator(15.0)], default=7.0)
    current_hba1c = models.FloatField(validators=[MinValueValidator(4.0), MaxValueValidator(15.0)], null=True, blank=True)
    
    # Insulin therapy
    insulin_regimen = models.CharField(max_length=20, choices=INSULIN_REGIMEN_CHOICES, default='none')
    total_daily_dose = models.FloatField(null=True, blank=True, help_text="Total daily insulin dose in units")
    carb_ratio = models.FloatField(null=True, blank=True, help_text="Insulin to carb ratio (1 unit per X grams)")
    correction_factor = models.FloatField(null=True, blank=True, help_text="Correction factor (1 unit drops BG by X mg/dL)")
    
    # Monitoring
    monitoring_method = models.CharField(max_length=20, choices=MONITORING_METHOD_CHOICES, default='bgm')
    target_glucose_min = models.IntegerField(default=80, help_text="Target glucose minimum (mg/dL)")
    target_glucose_max = models.IntegerField(default=130, help_text="Target glucose maximum (mg/dL)")
    
    # Complications
    has_retinopathy = models.BooleanField(default=False)
    has_nephropathy = models.BooleanField(default=False)
    has_neuropathy = models.BooleanField(default=False)
    has_cardiovascular_disease = models.BooleanField(default=False)
    
    # Lifestyle factors
    exercise_frequency = models.IntegerField(default=0, help_text="Exercise sessions per week")
    smoking_status = models.CharField(max_length=20, choices=[
        ('never', 'Never'),
        ('former', 'Former'),
        ('current', 'Current'),
    ], default='never')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.get_diabetes_type_display()}"

    class Meta:
        db_table = 'diabetes_patients'


class BloodGlucoseReading(models.Model):
    """Blood glucose measurements"""
    READING_TYPE_CHOICES = [
        ('fasting', 'Fasting'),
        ('pre_meal', 'Pre-meal'),
        ('post_meal', 'Post-meal'),
        ('bedtime', 'Bedtime'),
        ('random', 'Random'),
        ('exercise', 'Exercise'),
        ('sick', 'Sick Day'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='glucose_readings')
    reading_type = models.CharField(max_length=20, choices=READING_TYPE_CHOICES)
    glucose_value = models.IntegerField(validators=[MinValueValidator(20), MaxValueValidator(600)])
    reading_datetime = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    # Additional context
    meal_carbs = models.IntegerField(null=True, blank=True, help_text="Carbohydrates consumed (grams)")
    insulin_taken = models.FloatField(null=True, blank=True, help_text="Insulin units taken")
    exercise_minutes = models.IntegerField(null=True, blank=True, help_text="Exercise duration (minutes)")
    
    # Flags
    is_hypoglycemic = models.BooleanField(default=False)
    is_hyperglycemic = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-flag hypo/hyperglycemia
        self.is_hypoglycemic = self.glucose_value < 70
        self.is_hyperglycemic = self.glucose_value > 250
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.glucose_value} mg/dL"

    class Meta:
        db_table = 'blood_glucose_readings'
        ordering = ['-reading_datetime']


class HbA1cRecord(models.Model):
    """HbA1c test records"""
    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='hba1c_records')
    test_date = models.DateField()
    hba1c_value = models.FloatField(validators=[MinValueValidator(4.0), MaxValueValidator(15.0)])
    lab_name = models.CharField(max_length=100, blank=True)
    ordered_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Analysis
    is_at_target = models.BooleanField(default=False)
    change_from_previous = models.FloatField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Check if at target
        self.is_at_target = self.hba1c_value <= self.diabetes_patient.hba1c_target
        
        # Calculate change from previous
        previous_record = HbA1cRecord.objects.filter(
            diabetes_patient=self.diabetes_patient,
            test_date__lt=self.test_date
        ).order_by('-test_date').first()
        
        if previous_record:
            self.change_from_previous = self.hba1c_value - previous_record.hba1c_value
        
        super().save(*args, **kwargs)
        
        # Update current HbA1c in diabetes patient profile
        self.diabetes_patient.current_hba1c = self.hba1c_value
        self.diabetes_patient.save()

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.hba1c_value}%"

    class Meta:
        db_table = 'hba1c_records'
        ordering = ['-test_date']


class DiabetesMedication(models.Model):
    """Diabetes medications tracking"""
    MEDICATION_TYPE_CHOICES = [
        ('insulin_rapid', 'Rapid-acting Insulin'),
        ('insulin_short', 'Short-acting Insulin'),
        ('insulin_intermediate', 'Intermediate-acting Insulin'),
        ('insulin_long', 'Long-acting Insulin'),
        ('insulin_ultra_long', 'Ultra-long-acting Insulin'),
        ('metformin', 'Metformin'),
        ('sulfonylurea', 'Sulfonylurea'),
        ('dpp4_inhibitor', 'DPP-4 Inhibitor'),
        ('glp1_agonist', 'GLP-1 Agonist'),
        ('sglt2_inhibitor', 'SGLT-2 Inhibitor'),
        ('thiazolidinedione', 'Thiazolidinedione'),
        ('alpha_glucosidase', 'Alpha-glucosidase Inhibitor'),
        ('other', 'Other'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=100)
    medication_type = models.CharField(max_length=30, choices=MEDICATION_TYPE_CHOICES)
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    prescribed_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.medication_name}"

    class Meta:
        db_table = 'diabetes_medications'


class DiabetesComplicationScreening(models.Model):
    """Diabetes complications screening records"""
    SCREENING_TYPE_CHOICES = [
        ('retinopathy', 'Diabetic Retinopathy'),
        ('nephropathy', 'Diabetic Nephropathy'),
        ('neuropathy', 'Diabetic Neuropathy'),
        ('foot', 'Diabetic Foot'),
        ('cardiovascular', 'Cardiovascular'),
        ('dental', 'Dental'),
    ]
    
    RESULT_CHOICES = [
        ('normal', 'Normal'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('proliferative', 'Proliferative'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='screenings')
    screening_type = models.CharField(max_length=20, choices=SCREENING_TYPE_CHOICES)
    screening_date = models.DateField()
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    
    # Specific measurements
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    microalbumin = models.FloatField(null=True, blank=True)
    egfr = models.FloatField(null=True, blank=True)
    
    performed_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    next_screening_date = models.DateField(null=True, blank=True)
    
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.get_screening_type_display()}"

    class Meta:
        db_table = 'diabetes_complication_screenings'
        ordering = ['-screening_date']


class DiabetesEducationSession(models.Model):
    """Diabetes education and training sessions"""
    EDUCATION_TYPE_CHOICES = [
        ('initial', 'Initial Diabetes Education'),
        ('insulin_training', 'Insulin Injection Training'),
        ('bgm_training', 'Blood Glucose Monitoring Training'),
        ('carb_counting', 'Carbohydrate Counting'),
        ('exercise', 'Exercise and Diabetes'),
        ('sick_day', 'Sick Day Management'),
        ('hypoglycemia', 'Hypoglycemia Management'),
        ('foot_care', 'Foot Care'),
        ('travel', 'Travel with Diabetes'),
        ('technology', 'Diabetes Technology'),
        ('nutrition', 'Nutrition Counseling'),
        ('other', 'Other'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='education_sessions')
    education_type = models.CharField(max_length=20, choices=EDUCATION_TYPE_CHOICES)
    session_date = models.DateField()
    duration_minutes = models.IntegerField(default=60)
    
    educator = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    topics_covered = models.TextField()
    patient_understanding_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poor, 5=Excellent"
    )
    
    materials_provided = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    next_session_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.get_education_type_display()}"

    class Meta:
        db_table = 'diabetes_education_sessions'
        ordering = ['-session_date']


class DiabetesEmergencyEvent(models.Model):
    """Diabetes-related emergency events"""
    EVENT_TYPE_CHOICES = [
        ('hypoglycemia', 'Severe Hypoglycemia'),
        ('dka', 'Diabetic Ketoacidosis'),
        ('hhs', 'Hyperosmolar Hyperglycemic State'),
        ('hyperglycemia', 'Severe Hyperglycemia'),
        ('other', 'Other Emergency'),
    ]
    
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='emergency_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    event_datetime = models.DateTimeField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Clinical measurements
    glucose_level = models.IntegerField(null=True, blank=True)
    ketones = models.CharField(max_length=20, blank=True)
    symptoms = models.TextField()
    
    # Treatment
    treatment_given = models.TextField()
    hospital_admission = models.BooleanField(default=False)
    hospital_name = models.CharField(max_length=100, blank=True)
    
    # Outcomes
    resolution_datetime = models.DateTimeField(null=True, blank=True)
    outcome = models.TextField(blank=True)
    
    # Prevention
    contributing_factors = models.TextField(blank=True)
    prevention_plan = models.TextField(blank=True)
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.get_event_type_display()}"

    class Meta:
        db_table = 'diabetes_emergency_events'
        ordering = ['-event_datetime']


class DiabetesGoal(models.Model):
    """Patient diabetes management goals"""
    GOAL_TYPE_CHOICES = [
        ('hba1c', 'HbA1c Target'),
        ('weight', 'Weight Management'),
        ('exercise', 'Exercise Goal'),
        ('glucose', 'Glucose Control'),
        ('medication', 'Medication Adherence'),
        ('education', 'Education Completion'),
        ('screening', 'Screening Schedule'),
        ('lifestyle', 'Lifestyle Change'),
        ('other', 'Other Goal'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('modified', 'Modified'),
        ('discontinued', 'Discontinued'),
    ]

    diabetes_patient = models.ForeignKey(DiabetesPatient, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    target_value = models.FloatField(null=True, blank=True)
    current_value = models.FloatField(null=True, blank=True)
    target_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    set_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.diabetes_patient.patient.user.get_full_name()} - {self.title}"

    class Meta:
        db_table = 'diabetes_goals'
        ordering = ['-created_at']


# ================================
# S3 Data Management Models
# ================================

class MedicalInstitution(models.Model):
    """Model for medical institutions with S3 storage integration."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    license_number = models.CharField(max_length=50, unique=True)
    accreditation = models.CharField(max_length=100, blank=True)
    
    # S3 Configuration
    s3_prefix = models.CharField(max_length=100, unique=True, editable=False)
    storage_quota_gb = models.FloatField(default=1000.0)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.s3_prefix:
            self.s3_prefix = f"medicine/institutions/{self.id}"
        super().save(*args, **kwargs)
    
    @property
    def total_patients(self):
        return self.medicine_patients.filter(is_active=True).count()
    
    @property
    def total_records(self):
        return MedicalRecord.objects.filter(patient__institution=self).count()
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        db_table = 'medicine_institutions'
        ordering = ['name']


class MedicinePatient(models.Model):
    """Enhanced patient model with S3 integration for medical records."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(MedicalInstitution, on_delete=models.CASCADE, related_name='medicine_patients')
    
    # Patient Information
    patient_code = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    
    # Contact Information (encrypted in S3)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Medical Information
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    
    # Insurance Information (encrypted in S3)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    
    # S3 Configuration
    s3_patient_prefix = models.CharField(max_length=200, unique=True, editable=False)
    
    # Physical Measurements
    height_cm = models.FloatField(null=True, blank=True, help_text="Height in cm")
    weight_kg = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_medicine_patients')
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.s3_patient_prefix:
            self.s3_patient_prefix = f"{self.institution.s3_prefix}/patients/{self.id}"
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def bmi(self):
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 2)
        return None
    
    @property
    def total_records(self):
        return self.medical_records.count()
    
    @property
    def last_visit_date(self):
        last_consultation = self.consultations.order_by('-consultation_date').first()
        return last_visit_date.consultation_date if last_consultation else None
    
    def __str__(self):
        return f"{self.full_name} ({self.patient_code})"
    
    class Meta:
        db_table = 'medicine_patients_s3'
        unique_together = ['institution', 'patient_code']
        ordering = ['first_name', 'last_name']


class Consultation(models.Model):
    """Model for patient consultations with S3 note storage."""
    
    CONSULTATION_TYPE_CHOICES = [
        ('routine', 'Routine Check-up'),
        ('emergency', 'Emergency'),
        ('follow_up', 'Follow-up'),
        ('specialist', 'Specialist Consultation'),
        ('procedure', 'Procedure'),
        ('diagnostic', 'Diagnostic'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(MedicinePatient, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicine_consultations')
    
    # Consultation Information
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES)
    consultation_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    
    # Clinical Information
    chief_complaint = models.TextField()
    history_present_illness = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    
    # Vital Signs
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature in Celsius")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)
    
    # S3 Storage for detailed notes
    s3_notes_key = models.CharField(max_length=500, blank=True, default='')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.consultation_date.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        db_table = 'medicine_consultations'
        ordering = ['-consultation_date']


class LabResult(models.Model):
    """Model for lab results stored in S3."""
    
    TEST_CATEGORY_CHOICES = [
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('microbiology', 'Microbiology'),
        ('pathology', 'Pathology'),
        ('chemistry', 'Clinical Chemistry'),
        ('hematology', 'Hematology'),
        ('immunology', 'Immunology'),
        ('toxicology', 'Toxicology'),
    ]
    
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(MedicinePatient, on_delete=models.CASCADE, related_name='lab_results')
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results')
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ordered_lab_results')
    
    # Test Information
    test_name = models.CharField(max_length=200)
    test_category = models.CharField(max_length=20, choices=TEST_CATEGORY_CHOICES)
    lab_facility = models.CharField(max_length=200)
    
    # Dates
    ordered_date = models.DateTimeField()
    collection_date = models.DateTimeField(null=True, blank=True)
    result_date = models.DateTimeField(null=True, blank=True)
    
    # S3 Storage for results
    s3_result_key = models.CharField(max_length=500, blank=True, default='')
    has_abnormal_values = models.BooleanField(default=False)
    has_critical_values = models.BooleanField(default=False)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.test_name}"
    
    class Meta:
        db_table = 'medicine_lab_results'
        ordering = ['-ordered_date']


class MedicineAuditLog(models.Model):
    """Audit log for medicine S3 operations."""
    
    ACTION_CHOICES = [
        ('create_institution', 'Create Institution'),
        ('create_patient', 'Create Patient'),
        ('upload_record', 'Upload Medical Record'),
        ('create_consultation', 'Create Consultation'),
        ('create_treatment_plan', 'Create Treatment Plan'),
        ('upload_lab_result', 'Upload Lab Result'),
        ('access_record', 'Access Record'),
        ('delete_record', 'Delete Record'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action Information
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)
    
    # User Information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Context Information
    institution = models.ForeignKey(MedicalInstitution, on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey(MedicinePatient, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Audit Details
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} - {self.resource_type} - {self.timestamp}"
    
    class Meta:
        db_table = 'medicine_audit_logs'
        ordering = ['-timestamp']


class DoctorWorkspace(models.Model):
    """Model for doctor workspaces with S3 integration."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicine_workspace')
    institution = models.ForeignKey(MedicalInstitution, on_delete=models.CASCADE, related_name='doctor_workspaces')
    
    # Workspace Configuration
    specializations = models.JSONField(default=list)
    departments = models.JSONField(default=list)
    
    # S3 Configuration
    s3_workspace_prefix = models.CharField(max_length=200, unique=True, editable=False)
    
    # Statistics
    total_consultations = models.PositiveIntegerField(default=0)
    total_patients_treated = models.PositiveIntegerField(default=0)
    total_treatment_plans_created = models.PositiveIntegerField(default=0)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.s3_workspace_prefix:
            self.s3_workspace_prefix = f"{self.institution.s3_prefix}/doctors/{self.doctor.id}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} - {self.institution.name}"
    
    class Meta:
        db_table = 'medicine_doctor_workspaces'
        ordering = ['-last_activity']

