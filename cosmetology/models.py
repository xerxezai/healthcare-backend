from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import json
import uuid

User = get_user_model()

# S3 Data Management Models for Cosmetology

class CosmetologySalon(models.Model):
    """S3-integrated salon/institution model for cosmetology practices"""
    INSTITUTION_TYPES = [
        ('beauty_salon', 'Beauty Salon'),
        ('spa', 'Medical Spa'),
        ('clinic', 'Aesthetic Clinic'),
        ('dermatology_center', 'Dermatology Center'),
        ('wellness_center', 'Wellness Center'),
        ('cosmetic_surgery', 'Cosmetic Surgery Center'),
        ('training_academy', 'Beauty Training Academy'),
        ('product_lab', 'Product Development Lab'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ]
    
    salon_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=30, choices=INSTITUTION_TYPES)
    license_number = models.CharField(max_length=100, unique=True)
    accreditation_body = models.CharField(max_length=100, blank=True)
    head_aesthetician = models.CharField(max_length=200)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    
    # Operational Details
    operating_hours = models.CharField(max_length=200, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    
    # S3 Configuration
    s3_bucket = models.CharField(max_length=100, blank=True)
    s3_folder_path = models.CharField(max_length=200, blank=True)
    s3_folders = models.JSONField(default=dict, blank=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Cosmetology Salon"
        verbose_name_plural = "Cosmetology Salons"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_institution_type_display()}"

class CosmetologyClientS3(models.Model):
    """S3-integrated client model for beauty and aesthetic treatments"""
    GENDER_CHOICES = [
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other'),
    ]
    
    SKIN_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('dry', 'Dry'),
        ('oily', 'Oily'),
        ('combination', 'Combination'),
        ('sensitive', 'Sensitive'),
        ('mature', 'Mature'),
    ]
    
    FITZPATRICK_TYPES = [
        ('type_1', 'Type I - Very Fair'),
        ('type_2', 'Type II - Fair'),
        ('type_3', 'Type III - Medium'),
        ('type_4', 'Type IV - Olive'),
        ('type_5', 'Type V - Brown'),
        ('type_6', 'Type VI - Dark Brown'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ]
    
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    salon = models.ForeignKey(CosmetologySalon, on_delete=models.CASCADE, related_name='clients')
    client_external_id = models.CharField(max_length=50, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    referring_source = models.CharField(max_length=200, blank=True)
    
    # Beauty Profile
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, blank=True)
    fitzpatrick_scale = models.CharField(max_length=10, choices=FITZPATRICK_TYPES, blank=True)
    allergies = models.TextField(blank=True)
    skin_concerns = models.JSONField(default=list, blank=True)
    beauty_goals = models.JSONField(default=list, blank=True)
    
    # S3 Configuration
    s3_folder_path = models.CharField(max_length=300, blank=True)
    s3_folders = models.JSONField(default=dict, blank=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Cosmetology Client (S3)"
        verbose_name_plural = "Cosmetology Clients (S3)"
        ordering = ['-created_at']
        unique_together = [['salon', 'client_external_id']]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.salon.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

class CosmetologyTreatment(models.Model):
    """Treatment session model for cosmetology services"""
    TREATMENT_TYPES = [
        ('facial', 'Facial Treatment'),
        ('chemical_peel', 'Chemical Peel'),
        ('microdermabrasion', 'Microdermabrasion'),
        ('laser_treatment', 'Laser Treatment'),
        ('botox', 'Botox Treatment'),
        ('fillers', 'Dermal Fillers'),
        ('skin_rejuvenation', 'Skin Rejuvenation'),
        ('acne_treatment', 'Acne Treatment'),
        ('anti_aging', 'Anti-Aging Treatment'),
        ('hair_removal', 'Hair Removal'),
        ('body_contouring', 'Body Contouring'),
        ('makeup_session', 'Makeup Session'),
        ('consultation', 'Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    treatment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    salon = models.ForeignKey(CosmetologySalon, on_delete=models.CASCADE)
    client = models.ForeignKey(CosmetologyClientS3, on_delete=models.CASCADE, related_name='treatments')
    
    # Treatment Details
    treatment_type = models.CharField(max_length=30, choices=TREATMENT_TYPES)
    treatment_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    practitioner = models.CharField(max_length=200)
    
    # Treatment Information
    description = models.TextField()
    products_used = models.JSONField(default=list, blank=True)
    techniques_applied = models.JSONField(default=list, blank=True)
    equipment_used = models.JSONField(default=list, blank=True)
    
    # Results and Notes
    treatment_notes = models.TextField(blank=True)
    client_feedback = models.TextField(blank=True)
    practitioner_observations = models.TextField(blank=True)
    before_photos = models.JSONField(default=list, blank=True)
    after_photos = models.JSONField(default=list, blank=True)
    
    # Follow-up
    next_appointment_recommended = models.DateField(null=True, blank=True)
    home_care_instructions = models.TextField(blank=True)
    
    # Pricing
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cosmetology Treatment"
        verbose_name_plural = "Cosmetology Treatments"
        ordering = ['-treatment_date']
    
    def __str__(self):
        return f"{self.get_treatment_type_display()} - {self.client.full_name} ({self.treatment_date.date()})"

class CosmetologyFile(models.Model):
    """S3 file management model for cosmetology documents and media"""
    FILE_CATEGORIES = [
        ('before_after_photos', 'Before/After Photos'),
        ('treatment_plans', 'Treatment Plans'),
        ('skin_analysis', 'Skin Analysis Reports'),
        ('client_consultations', 'Client Consultations'),
        ('procedure_documentation', 'Procedure Documentation'),
        ('product_formulations', 'Product Formulations'),
        ('allergy_patch_tests', 'Allergy & Patch Tests'),
        ('progress_tracking', 'Progress Tracking'),
        ('product_recommendations', 'Product Recommendations'),
        ('training_materials', 'Training Materials'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    file_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    salon = models.ForeignKey(CosmetologySalon, on_delete=models.CASCADE)
    client = models.ForeignKey(CosmetologyClientS3, on_delete=models.CASCADE, null=True, blank=True)
    
    # File Information
    original_name = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=FILE_CATEGORIES)
    
    # S3 Information
    s3_key = models.CharField(max_length=500)
    s3_bucket = models.CharField(max_length=100)
    s3_url = models.URLField(blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status and Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    upload_date = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Cosmetology File"
        verbose_name_plural = "Cosmetology Files"
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.original_name} - {self.get_category_display()}"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

class CosmetologyAnalysis(models.Model):
    """AI analysis results for cosmetology files and treatments"""
    ANALYSIS_TYPES = [
        ('skin_condition_analysis', 'Skin Condition Analysis'),
        ('aging_assessment', 'Aging Assessment'),
        ('color_matching', 'Color Matching'),
        ('treatment_effectiveness', 'Treatment Effectiveness'),
        ('product_recommendation', 'Product Recommendation'),
        ('facial_symmetry', 'Facial Symmetry Analysis'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('validated', 'Validated'),
    ]
    
    analysis_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    salon = models.ForeignKey(CosmetologySalon, on_delete=models.CASCADE)
    client = models.ForeignKey(CosmetologyClientS3, on_delete=models.CASCADE, null=True, blank=True)
    file = models.ForeignKey(CosmetologyFile, on_delete=models.CASCADE, null=True, blank=True)
    
    # Analysis Details
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPES)
    analysis_date = models.DateTimeField(auto_now_add=True)
    ai_model_used = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Results
    analysis_results = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list, blank=True)
    risk_factors = models.JSONField(default=list, blank=True)
    follow_up_needed = models.BooleanField(default=False)
    
    # Validation
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    validation_date = models.DateTimeField(null=True, blank=True)
    validation_notes = models.TextField(blank=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Cosmetology Analysis"
        verbose_name_plural = "Cosmetology Analyses"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.analysis_date.date()}"

class CosmetologyClient(models.Model):
    """Client model for cosmetology services"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    SKIN_TYPE_CHOICES = [
        ('oily', 'Oily'),
        ('dry', 'Dry'),
        ('combination', 'Combination'),
        ('sensitive', 'Sensitive'),
        ('normal', 'Normal'),
        ('acne_prone', 'Acne Prone'),
        ('mature', 'Mature'),
    ]
    
    HAIR_TYPE_CHOICES = [
        ('straight', 'Straight'),
        ('wavy', 'Wavy'),
        ('curly', 'Curly'),
        ('coily', 'Coily'),
        ('fine', 'Fine'),
        ('thick', 'Thick'),
        ('damaged', 'Damaged'),
        ('color_treated', 'Color Treated'),
    ]
    
    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Beauty profile
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES)
    hair_type = models.CharField(max_length=20, choices=HAIR_TYPE_CHOICES)
    allergies = models.TextField(blank=True, help_text="Known allergies to products or ingredients")
    skin_concerns = models.JSONField(default=list, help_text="List of skin concerns")
    hair_concerns = models.JSONField(default=list, help_text="List of hair concerns")
    
    # Preferences
    preferred_brands = models.JSONField(default=list, help_text="Preferred cosmetic brands")
    budget_range = models.CharField(max_length=50, blank=True)
    lifestyle_notes = models.TextField(blank=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.age}y {self.gender}"
    
    class Meta:
        ordering = ['-created_at']

class CosmetologyService(models.Model):
    """Available cosmetology services"""
    SERVICE_CATEGORIES = [
        ('facial', 'Facial Treatments'),
        ('hair', 'Hair Services'),
        ('nails', 'Nail Services'),
        ('makeup', 'Makeup Services'),
        ('body', 'Body Treatments'),
        ('laser', 'Laser Treatments'),
        ('injectable', 'Injectable Treatments'),
        ('skincare', 'Advanced Skincare'),
        ('permanent', 'Permanent Makeup'),
        ('wellness', 'Wellness & Spa'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Requirements and contraindications
    requirements = models.JSONField(default=list, help_text="Pre-service requirements")
    contraindications = models.JSONField(default=list, help_text="Contraindications")
    aftercare_instructions = models.TextField(blank=True)
    
    # Scheduling
    requires_consultation = models.BooleanField(default=False)
    session_gap_days = models.PositiveIntegerField(default=0, help_text="Minimum days between sessions")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        ordering = ['category', 'name']

class CosmetologyProduct(models.Model):
    """Cosmetic products and tools"""
    PRODUCT_TYPES = [
        ('skincare', 'Skincare'),
        ('makeup', 'Makeup'),
        ('haircare', 'Hair Care'),
        ('nailcare', 'Nail Care'),
        ('tools', 'Tools & Equipment'),
        ('supplements', 'Beauty Supplements'),
        ('professional', 'Professional Use Only'),
    ]
    
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    description = models.TextField()
    
    # Product details
    ingredients = models.JSONField(default=list, help_text="List of key ingredients")
    benefits = models.JSONField(default=list, help_text="Product benefits")
    skin_types = models.JSONField(default=list, help_text="Suitable skin types")
    usage_instructions = models.TextField(blank=True)
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Safety
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True)
    safety_warnings = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.brand} - {self.name}"
    
    class Meta:
        ordering = ['brand', 'name']

class CosmetologyAppointment(models.Model):
    """Client appointments for cosmetology services"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    client = models.ForeignKey(CosmetologyClient, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(CosmetologyService, on_delete=models.CASCADE)
    cosmetologist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cosmetology_appointments')
    
    # Scheduling
    appointment_date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Consultation and notes
    consultation_notes = models.TextField(blank=True, help_text="Pre-service consultation notes")
    service_notes = models.TextField(blank=True, help_text="Notes during service")
    aftercare_given = models.BooleanField(default=False)
    
    # Pricing
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Follow-up
    next_appointment_due = models.DateField(blank=True, null=True)
    follow_up_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.service_price + self.additional_charges - self.discount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.client.name} - {self.service.name} on {self.appointment_date.date()}"
    
    class Meta:
        ordering = ['-appointment_date']

class CosmetologyTreatmentPlan(models.Model):
    """Comprehensive treatment plans for clients"""
    client = models.ForeignKey(CosmetologyClient, on_delete=models.CASCADE, related_name='treatment_plans')
    cosmetologist = models.ForeignKey(User, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200, help_text="Treatment plan name")
    description = models.TextField()
    
    # Goals and timeline
    beauty_goals = models.JSONField(default=list, help_text="Client's beauty goals")
    target_concerns = models.JSONField(default=list, help_text="Specific concerns to address")
    duration_weeks = models.PositiveIntegerField(help_text="Expected duration in weeks")
    
    # Services and products
    recommended_services = models.ManyToManyField(CosmetologyService, through='TreatmentPlanService')
    recommended_products = models.ManyToManyField(CosmetologyProduct, through='TreatmentPlanProduct')
    
    # Tracking
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    progress_notes = models.TextField(blank=True)
    
    # Estimated costs
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} for {self.client.name}"
    
    class Meta:
        ordering = ['-created_at']

class TreatmentPlanService(models.Model):
    """Services included in a treatment plan"""
    treatment_plan = models.ForeignKey(CosmetologyTreatmentPlan, on_delete=models.CASCADE)
    service = models.ForeignKey(CosmetologyService, on_delete=models.CASCADE)
    
    frequency = models.CharField(max_length=100, help_text="e.g., 'Weekly', 'Every 2 weeks'")
    sessions_count = models.PositiveIntegerField(help_text="Total number of sessions")
    sessions_completed = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0, help_text="Order in treatment sequence")
    
    notes = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'service__name']

class TreatmentPlanProduct(models.Model):
    """Products recommended in a treatment plan"""
    treatment_plan = models.ForeignKey(CosmetologyTreatmentPlan, on_delete=models.CASCADE)
    product = models.ForeignKey(CosmetologyProduct, on_delete=models.CASCADE)
    
    usage_frequency = models.CharField(max_length=100, help_text="e.g., 'Daily', 'Twice a week'")
    quantity_needed = models.PositiveIntegerField(help_text="Quantity for full treatment")
    priority = models.CharField(max_length=20, choices=[
        ('essential', 'Essential'),
        ('recommended', 'Recommended'),
        ('optional', 'Optional'),
    ], default='recommended')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['priority', 'product__name']

class CosmetologyConsultation(models.Model):
    """Initial consultation records"""
    client = models.ForeignKey(CosmetologyClient, on_delete=models.CASCADE, related_name='consultations')
    cosmetologist = models.ForeignKey(User, on_delete=models.CASCADE)
    
    consultation_date = models.DateTimeField()
    
    # Skin analysis
    skin_analysis = models.JSONField(default=dict, help_text="Detailed skin analysis results")
    skin_photos = models.JSONField(default=list, help_text="Photo references")
    
    # Hair analysis
    hair_analysis = models.JSONField(default=dict, help_text="Hair condition analysis")
    scalp_condition = models.TextField(blank=True)
    
    # Goals and concerns
    primary_concerns = models.TextField()
    beauty_goals = models.TextField()
    lifestyle_factors = models.TextField(blank=True)
    
    # Recommendations
    immediate_recommendations = models.TextField()
    long_term_plan = models.TextField(blank=True)
    product_recommendations = models.TextField(blank=True)
    
    # Follow-up
    next_consultation_date = models.DateField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Consultation for {self.client.name} on {self.consultation_date.date()}"
    
    class Meta:
        ordering = ['-consultation_date']

class CosmetologyProgress(models.Model):
    """Progress tracking for ongoing treatments"""
    client = models.ForeignKey(CosmetologyClient, on_delete=models.CASCADE, related_name='progress_records')
    treatment_plan = models.ForeignKey(CosmetologyTreatmentPlan, on_delete=models.CASCADE, blank=True, null=True)
    
    date_recorded = models.DateField()
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Progress measurements
    progress_photos = models.JSONField(default=list, help_text="Progress photo references")
    measurements = models.JSONField(default=dict, help_text="Skin measurements, etc.")
    improvements_noted = models.TextField()
    concerns_remaining = models.TextField(blank=True)
    
    # Client feedback
    client_satisfaction = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)], 
        help_text="Client satisfaction rating 1-10"
    )
    client_feedback = models.TextField(blank=True)
    
    # Next steps
    recommendations = models.TextField(blank=True)
    plan_adjustments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Progress for {self.client.name} on {self.date_recorded}"
    
    class Meta:
        ordering = ['-date_recorded']


# =============== COSMETIC GYNECOLOGY MODELS ===============

class CosmeticGynecologyClient(models.Model):
    """Specialized client model for cosmetic gynecology services"""
    CONCERN_TYPES = [
        ('vaginal_laxity', 'Vaginal Laxity'),
        ('labial_asymmetry', 'Labial Asymmetry'),
        ('vulvar_discoloration', 'Vulvar Discoloration'),
        ('intimate_dryness', 'Intimate Dryness'),
        ('post_pregnancy', 'Post-Pregnancy Changes'),
        ('menopause_effects', 'Menopause Effects'),
        ('intimate_rejuvenation', 'Intimate Rejuvenation'),
        ('confidence_enhancement', 'Confidence Enhancement'),
    ]
    
    PREVIOUS_TREATMENTS = [
        ('none', 'None'),
        ('laser_therapy', 'Laser Therapy'),
        ('radiofrequency', 'Radiofrequency'),
        ('platelet_therapy', 'Platelet Rich Plasma'),
        ('surgical', 'Surgical Procedures'),
        ('topical_treatments', 'Topical Treatments'),
        ('hormone_therapy', 'Hormone Therapy'),
    ]
    
    # Link to main cosmetology client
    cosmetology_client = models.OneToOneField(
        CosmetologyClient, 
        on_delete=models.CASCADE,
        related_name='gynecology_profile'
    )
    
    # Specialized information
    age_at_first_pregnancy = models.PositiveIntegerField(null=True, blank=True)
    number_of_pregnancies = models.PositiveIntegerField(default=0)
    number_of_deliveries = models.PositiveIntegerField(default=0)
    c_section_history = models.BooleanField(default=False)
    menopause_status = models.BooleanField(default=False)
    hormonal_therapy = models.BooleanField(default=False)
    
    # Primary concerns
    primary_concerns = models.JSONField(default=list, help_text="List of primary aesthetic concerns")
    concern_severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Severity of concerns (1-10 scale)"
    )
    
    # Medical history
    gynecological_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    previous_treatments = models.CharField(max_length=50, choices=PREVIOUS_TREATMENTS, default='none')
    treatment_satisfaction = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True,
        help_text="Satisfaction with previous treatments (1-10)"
    )
    
    # Goals and expectations
    treatment_goals = models.TextField(help_text="Client's specific goals and expectations")
    lifestyle_factors = models.TextField(blank=True, help_text="Exercise, diet, stress factors")
    
    # AI Analysis fields
    ai_risk_assessment = models.JSONField(default=dict, blank=True)
    ai_treatment_recommendations = models.JSONField(default=dict, blank=True)
    ai_recovery_prediction = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Gynecology Profile - {self.cosmetology_client.name}"


class CosmeticGynecologyTreatment(models.Model):
    """Specialized treatments for cosmetic gynecology"""
    TREATMENT_CATEGORIES = [
        ('non_invasive', 'Non-Invasive'),
        ('minimally_invasive', 'Minimally Invasive'),
        ('surgical', 'Surgical'),
        ('combination', 'Combination Therapy'),
    ]
    
    TECHNOLOGY_TYPES = [
        ('laser_co2', 'CO2 Laser'),
        ('laser_erbium', 'Erbium Laser'),
        ('radiofrequency', 'Radiofrequency'),
        ('ultrasound_focused', 'Focused Ultrasound'),
        ('platelet_therapy', 'Platelet Rich Plasma'),
        ('stem_cell', 'Stem Cell Therapy'),
        ('filler_injection', 'Hyaluronic Acid Fillers'),
        ('surgical_procedure', 'Surgical Procedure'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=TREATMENT_CATEGORIES)
    technology_used = models.CharField(max_length=30, choices=TECHNOLOGY_TYPES)
    
    description = models.TextField()
    indications = models.TextField(help_text="Conditions this treatment addresses")
    contraindications = models.TextField(help_text="When this treatment should not be used")
    
    # Treatment details
    duration_minutes = models.PositiveIntegerField(help_text="Treatment duration in minutes")
    sessions_required = models.PositiveIntegerField(help_text="Number of sessions typically required")
    interval_between_sessions = models.PositiveIntegerField(help_text="Days between sessions")
    
    # Recovery and aftercare
    downtime_days = models.PositiveIntegerField(help_text="Expected downtime in days")
    recovery_instructions = models.TextField()
    follow_up_schedule = models.TextField()
    
    # Effectiveness and safety
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Success rate percentage")
    side_effects = models.TextField(help_text="Potential side effects and risks")
    
    # Pricing
    price_per_session = models.DecimalField(max_digits=10, decimal_places=2)
    package_pricing = models.JSONField(default=dict, blank=True)
    
    # AI optimization
    ai_suitability_criteria = models.JSONField(default=dict, blank=True)
    ai_outcome_predictors = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class CosmeticGynecologyConsultation(models.Model):
    """AI-powered consultation for cosmetic gynecology"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('follow_up', 'Follow-up Required'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(CosmeticGynecologyClient, on_delete=models.CASCADE)
    consultation_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Assessment data
    chief_complaints = models.TextField()
    physical_examination = models.TextField(blank=True)
    client_expectations = models.TextField()
    psychological_readiness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Psychological readiness for treatment (1-10)"
    )
    
    # AI Analysis Results
    ai_analysis_complete = models.BooleanField(default=False)
    ai_risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_recommended_treatments = models.JSONField(default=list, blank=True)
    ai_treatment_timeline = models.JSONField(default=dict, blank=True)
    ai_expected_outcomes = models.JSONField(default=dict, blank=True)
    ai_contraindications = models.JSONField(default=list, blank=True)
    
    # Professional assessment
    doctor_notes = models.TextField(blank=True)
    recommended_treatment_plan = models.ForeignKey(
        'CosmeticGynecologyTreatmentPlan',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    # Follow-up
    next_consultation = models.DateTimeField(null=True, blank=True)
    consultation_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Consultation - {self.client.cosmetology_client.name} on {self.consultation_date.date()}"


class CosmeticGynecologyTreatmentPlan(models.Model):
    """Comprehensive treatment plan with AI optimization"""
    PLAN_STATUS = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('modified', 'Modified'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(CosmeticGynecologyClient, on_delete=models.CASCADE)
    consultation = models.ForeignKey(CosmeticGynecologyConsultation, on_delete=models.CASCADE)
    
    plan_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='draft')
    
    # Treatment details
    primary_treatments = models.ManyToManyField(CosmeticGynecologyTreatment, related_name='primary_plans')
    supporting_treatments = models.ManyToManyField(
        CosmeticGynecologyTreatment, 
        related_name='supporting_plans', 
        blank=True
    )
    
    # Timeline and scheduling
    start_date = models.DateField()
    estimated_completion = models.DateField()
    total_sessions = models.PositiveIntegerField()
    session_interval_days = models.PositiveIntegerField()
    
    # AI-powered optimization
    ai_plan_optimization = models.JSONField(default=dict, blank=True)
    ai_success_probability = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_risk_mitigation = models.JSONField(default=dict, blank=True)
    ai_personalization_factors = models.JSONField(default=dict, blank=True)
    
    # Cost and insurance
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    payment_plan = models.JSONField(default=dict, blank=True)
    insurance_coverage = models.TextField(blank=True)
    
    # Monitoring and adjustments
    progress_milestones = models.JSONField(default=list, blank=True)
    modification_history = models.JSONField(default=list, blank=True)
    
    # Consent and documentation
    informed_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    treatment_agreement = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Treatment Plan: {self.plan_name} - {self.client.cosmetology_client.name}"


class CosmeticGynecologyProgress(models.Model):
    """Track treatment progress with AI-powered analysis"""
    treatment_plan = models.ForeignKey(CosmeticGynecologyTreatmentPlan, on_delete=models.CASCADE)
    session_number = models.PositiveIntegerField()
    session_date = models.DateTimeField()
    
    # Session details
    treatment_performed = models.ForeignKey(CosmeticGynecologyTreatment, on_delete=models.CASCADE)
    session_notes = models.TextField()
    client_comfort_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Client comfort during session (1-10)"
    )
    
    # Progress assessment
    before_photos = models.JSONField(default=list, blank=True, help_text="Before session photo URLs")
    after_photos = models.JSONField(default=list, blank=True, help_text="After session photo URLs")
    
    # AI-powered progress analysis
    ai_progress_analysis = models.JSONField(default=dict, blank=True)
    ai_improvement_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_next_session_recommendations = models.JSONField(default=dict, blank=True)
    ai_treatment_adjustments = models.JSONField(default=dict, blank=True)
    
    # Client feedback
    client_satisfaction = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Client satisfaction with session (1-10)"
    )
    client_feedback = models.TextField(blank=True)
    side_effects_reported = models.TextField(blank=True)
    
    # Recovery tracking
    healing_progress = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Healing progress assessment (1-10)"
    )
    recovery_notes = models.TextField(blank=True)
    
    # Next steps
    next_session_date = models.DateTimeField(null=True, blank=True)
    homecare_instructions = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Session {self.session_number} - {self.treatment_plan.client.cosmetology_client.name}"
    
    class Meta:
        ordering = ['session_number']
