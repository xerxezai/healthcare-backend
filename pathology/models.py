from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class PathologyDepartment(models.Model):
    """Pathology Department/Laboratory Information"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    head_pathologist = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='headed_pathology_departments'
    )
    is_active = models.BooleanField(default=True)
    accreditation_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Department"
        verbose_name_plural = "Pathology Departments"

    def __str__(self):
        return f"{self.name} ({self.code})"


class PathologyTest(models.Model):
    """Pathology Test Types and Templates"""
    TEST_CATEGORIES = [
        ('histopathology', 'Histopathology'),
        ('cytopathology', 'Cytopathology'),
        ('hematology', 'Hematology'),
        ('clinical_chemistry', 'Clinical Chemistry'),
        ('microbiology', 'Microbiology'),
        ('immunology', 'Immunology'),
        ('molecular', 'Molecular Pathology'),
        ('genetic', 'Genetic Testing'),
        ('forensic', 'Forensic Pathology'),
        ('autopsy', 'Autopsy'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, choices=TEST_CATEGORIES)
    description = models.TextField(blank=True)
    specimen_type = models.CharField(max_length=100)
    normal_range = models.TextField(blank=True, help_text="Normal reference values")
    test_methodology = models.CharField(max_length=200, blank=True)
    processing_time_hours = models.PositiveIntegerField(default=24)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    requires_fasting = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Test"
        verbose_name_plural = "Pathology Tests"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Patient(models.Model):
    """Patient Information for Pathology"""
    patient_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    medical_record_number = models.CharField(max_length=50, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class PathologyOrder(models.Model):
    """Pathology Test Orders"""
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('collected', 'Specimen Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_LEVELS = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
        ('critical', 'Critical'),
    ]

    order_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pathology_orders')
    ordering_physician = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ordered_pathology_tests'
    )
    department = models.ForeignKey(PathologyDepartment, on_delete=models.CASCADE)
    tests = models.ManyToManyField(PathologyTest, through='PathologyOrderTest')
    order_date = models.DateTimeField(auto_now_add=True)
    collection_date = models.DateTimeField(null=True, blank=True)
    expected_completion = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='routine')
    clinical_history = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_pathology_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Order"
        verbose_name_plural = "Pathology Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.patient.full_name}"


class PathologyOrderTest(models.Model):
    """Individual tests within a pathology order"""
    order = models.ForeignKey(PathologyOrder, on_delete=models.CASCADE)
    test = models.ForeignKey(PathologyTest, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PathologyOrder.ORDER_STATUS, default='pending')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_pathology_tests'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pathology Order Test"
        verbose_name_plural = "Pathology Order Tests"
        unique_together = ['order', 'test']

    def __str__(self):
        return f"{self.order.order_id} - {self.test.name}"


class Specimen(models.Model):
    """Specimen/Sample Information"""
    SPECIMEN_TYPES = [
        ('blood', 'Blood'),
        ('urine', 'Urine'),
        ('tissue', 'Tissue'),
        ('biopsy', 'Biopsy'),
        ('cytology', 'Cytology'),
        ('fluid', 'Body Fluid'),
        ('swab', 'Swab'),
        ('stool', 'Stool'),
        ('sputum', 'Sputum'),
        ('bone_marrow', 'Bone Marrow'),
        ('other', 'Other'),
    ]

    SPECIMEN_STATUS = [
        ('collected', 'Collected'),
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('stored', 'Stored'),
        ('discarded', 'Discarded'),
        ('contaminated', 'Contaminated'),
        ('insufficient', 'Insufficient'),
    ]

    specimen_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    order = models.ForeignKey(PathologyOrder, on_delete=models.CASCADE, related_name='specimens')
    specimen_type = models.CharField(max_length=50, choices=SPECIMEN_TYPES)
    collection_site = models.CharField(max_length=200, blank=True)
    collection_method = models.CharField(max_length=200, blank=True)
    collected_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='collected_specimens'
    )
    collection_datetime = models.DateTimeField()
    received_datetime = models.DateTimeField(null=True, blank=True)
    volume_quantity = models.CharField(max_length=100, blank=True)
    container_type = models.CharField(max_length=100, blank=True)
    preservative = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=SPECIMEN_STATUS, default='collected')
    storage_location = models.CharField(max_length=200, blank=True)
    storage_temperature = models.CharField(max_length=50, blank=True)
    quality_assessment = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Specimen"
        verbose_name_plural = "Specimens"
        ordering = ['-collection_datetime']

    def __str__(self):
        return f"Specimen {self.specimen_id} - {self.specimen_type}"


class PathologyReport(models.Model):
    """Pathology Test Results and Reports"""
    REPORT_STATUS = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('finalized', 'Finalized'),
        ('amended', 'Amended'),
        ('cancelled', 'Cancelled'),
    ]

    RESULT_STATUS = [
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal'),
        ('critical', 'Critical'),
        ('inconclusive', 'Inconclusive'),
    ]

    report_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    order_test = models.OneToOneField(PathologyOrderTest, on_delete=models.CASCADE, related_name='report')
    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, related_name='reports')
    pathologist = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='pathology_reports'
    )
    
    # Microscopic Findings
    gross_description = models.TextField(blank=True, help_text="Macroscopic/Gross examination")
    microscopic_description = models.TextField(blank=True, help_text="Microscopic examination")
    
    # Results
    test_results = models.JSONField(default=dict, help_text="Structured test results")
    interpretation = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Technical Details
    staining_methods = models.CharField(max_length=500, blank=True)
    special_studies = models.TextField(blank=True)
    immunohistochemistry = models.TextField(blank=True)
    molecular_findings = models.TextField(blank=True)
    
    # Status and Quality
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS, default='normal')
    confidence_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Confidence level 1-5"
    )
    
    # Timing
    reported_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Info
    technical_notes = models.TextField(blank=True)
    quality_control_notes = models.TextField(blank=True)
    amendments = models.TextField(blank=True)
    
    # Images and Attachments
    digital_slides = models.JSONField(default=list, help_text="Digital slide image paths")
    attachments = models.JSONField(default=list, help_text="Additional file attachments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Report"
        verbose_name_plural = "Pathology Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.report_id} - {self.order_test.test.name}"


class DigitalSlide(models.Model):
    """Digital Microscopy Slides"""
    slide_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    report = models.ForeignKey(PathologyReport, on_delete=models.CASCADE, related_name='slides')
    title = models.CharField(max_length=200)
    stain_type = models.CharField(max_length=100, blank=True)
    magnification = models.CharField(max_length=50, blank=True)
    image_path = models.CharField(max_length=500)
    thumbnail_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    resolution = models.CharField(max_length=50, blank=True)
    format = models.CharField(max_length=20, blank=True)
    annotations = models.JSONField(default=list, help_text="Image annotations and markings")
    ai_analysis = models.JSONField(default=dict, help_text="AI-assisted analysis results")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Digital Slide"
        verbose_name_plural = "Digital Slides"
        ordering = ['-created_at']

    def __str__(self):
        return f"Slide {self.slide_id} - {self.title}"


class PathologyQualityControl(models.Model):
    """Quality Control for Pathology Lab"""
    QC_TYPES = [
        ('equipment', 'Equipment Check'),
        ('reagent', 'Reagent Quality'),
        ('proficiency', 'Proficiency Testing'),
        ('calibration', 'Calibration'),
        ('maintenance', 'Maintenance'),
        ('training', 'Staff Training'),
    ]

    qc_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    qc_type = models.CharField(max_length=20, choices=QC_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    performed_date = models.DateTimeField()
    equipment_instrument = models.CharField(max_length=200, blank=True)
    results = models.JSONField(default=dict)
    passed = models.BooleanField(default=True)
    corrective_actions = models.TextField(blank=True)
    next_due_date = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quality Control"
        verbose_name_plural = "Quality Controls"
        ordering = ['-performed_date']

    def __str__(self):
        return f"QC {self.qc_id} - {self.title}"


# S3 Data Management Models

class PathologyLaboratory(models.Model):
    """Extended laboratory model for S3 data management"""
    LABORATORY_TYPES = [
        ('clinical', 'Clinical Laboratory'),
        ('anatomical', 'Anatomical Pathology'),
        ('molecular', 'Molecular Diagnostics'),
        ('cytogenetics', 'Cytogenetics'),
        ('hematology', 'Hematology Lab'),
        ('microbiology', 'Microbiology Lab'),
        ('immunology', 'Immunology Lab'),
        ('research', 'Research Laboratory'),
    ]
    
    name = models.CharField(max_length=200)
    laboratory_type = models.CharField(max_length=50, choices=LABORATORY_TYPES)
    license_number = models.CharField(max_length=100, unique=True)
    accreditation_body = models.CharField(max_length=100, blank=True)
    director_name = models.CharField(max_length=200)
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
    specializations = models.JSONField(default=list, help_text="Laboratory specializations")
    equipment_list = models.JSONField(default=list, help_text="Major equipment and instruments")
    certification_info = models.JSONField(default=dict, help_text="Certification details")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Laboratory"
        verbose_name_plural = "Pathology Laboratories"

    def __str__(self):
        return f"{self.name} ({self.laboratory_type})"


class PathologyPatient(models.Model):
    """Extended patient model for S3 data management"""
    patient_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    medical_record_number = models.CharField(max_length=50, blank=True)
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    referring_physician = models.CharField(max_length=200, blank=True)
    medical_history = models.JSONField(default=list, help_text="Medical history entries")
    allergies = models.JSONField(default=list, help_text="Known allergies")
    medications = models.JSONField(default=list, help_text="Current medications")
    laboratory = models.ForeignKey(PathologyLaboratory, on_delete=models.CASCADE, related_name='patients')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Patient"
        verbose_name_plural = "Pathology Patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class PathologySpecimen(models.Model):
    """Specimen management for pathology"""
    SPECIMEN_TYPES = [
        ('tissue', 'Tissue Biopsy'),
        ('blood', 'Blood Sample'),
        ('urine', 'Urine Sample'),
        ('cytology', 'Cytology Sample'),
        ('fluid', 'Body Fluid'),
        ('swab', 'Swab Sample'),
        ('bone_marrow', 'Bone Marrow'),
        ('csf', 'Cerebrospinal Fluid'),
        ('sputum', 'Sputum'),
        ('stool', 'Stool Sample'),
    ]
    
    SPECIMEN_STATUS = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('sectioned', 'Sectioned'),
        ('stained', 'Stained'),
        ('reviewed', 'Under Review'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    specimen_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(PathologyPatient, on_delete=models.CASCADE, related_name='specimens')
    laboratory = models.ForeignKey(PathologyLaboratory, on_delete=models.CASCADE, related_name='specimens')
    specimen_type = models.CharField(max_length=50, choices=SPECIMEN_TYPES)
    collection_date = models.DateTimeField()
    received_date = models.DateTimeField(auto_now_add=True)
    collection_site = models.CharField(max_length=200, blank=True)
    collection_method = models.CharField(max_length=200, blank=True)
    volume_amount = models.CharField(max_length=100, blank=True)
    preservation_method = models.CharField(max_length=200, blank=True)
    storage_location = models.CharField(max_length=200, blank=True)
    storage_temperature = models.CharField(max_length=50, blank=True)
    clinical_info = models.TextField(blank=True)
    special_handling = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SPECIMEN_STATUS, default='received')
    processing_notes = models.TextField(blank=True)
    quality_indicators = models.JSONField(default=dict, help_text="Quality assessment indicators")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Specimen"
        verbose_name_plural = "Pathology Specimens"

    def __str__(self):
        return f"Specimen {self.specimen_id} - {self.specimen_type}"


class PathologyFile(models.Model):
    """File management for pathology data in S3"""
    FILE_TYPES = [
        ('microscopy', 'Microscopy Images'),
        ('lab_reports', 'Laboratory Reports'),
        ('test_results', 'Test Results'),
        ('pathology_slides', 'Pathology Slides'),
        ('imaging_studies', 'Imaging Studies'),
        ('documentation', 'Documentation'),
        ('quality_control', 'Quality Control'),
        ('calibration', 'Calibration Records'),
        ('patient_records', 'Patient Records'),
        ('regulatory', 'Regulatory Documents'),
    ]
    
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, choices=FILE_TYPES)
    s3_key = models.CharField(max_length=500, unique=True)
    s3_url = models.URLField(max_length=1000)
    laboratory = models.ForeignKey(PathologyLaboratory, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    patient = models.ForeignKey(PathologyPatient, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    specimen = models.ForeignKey(PathologySpecimen, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    size = models.BigIntegerField(default=0, help_text="File size in bytes")
    content_type = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, help_text="Additional file metadata")
    description = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_pathology_files', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology File"
        verbose_name_plural = "Pathology Files"

    def __str__(self):
        return f"{self.name} ({self.file_type})"


class PathologyAnalysis(models.Model):
    """AI/ML analysis results for pathology files"""
    ANALYSIS_TYPES = [
        ('cell_morphology', 'Cell Morphology Analysis'),
        ('cancer_detection', 'Cancer Detection'),
        ('tissue_classification', 'Tissue Classification'),
        ('stain_analysis', 'Stain Analysis'),
        ('cell_counting', 'Cell Counting'),
        ('abnormality_detection', 'Abnormality Detection'),
        ('image_enhancement', 'Image Enhancement'),
        ('quality_assessment', 'Quality Assessment'),
    ]
    
    ANALYSIS_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    file = models.ForeignKey(PathologyFile, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS, default='pending')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Analysis confidence score (0-1)")
    results = models.JSONField(default=dict, help_text="Detailed analysis results")
    processing_time = models.DurationField(null=True, blank=True)
    algorithm_version = models.CharField(max_length=50, blank=True)
    parameters_used = models.JSONField(default=dict, help_text="Analysis parameters")
    error_message = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_pathology_analyses')
    review_notes = models.TextField(blank=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pathology Analysis"
        verbose_name_plural = "Pathology Analyses"

    def __str__(self):
        return f"{self.analysis_type} - {self.file.name} ({self.status})"
