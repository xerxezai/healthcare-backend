# Diabetic Retinopathy Models for Medicine App
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class RetinopathyScreening(models.Model):
    """Model for diabetic retinopathy screening records"""
    SEVERITY_CHOICES = [
        ('none', 'No Retinopathy'),
        ('mild', 'Mild NPDR'),
        ('moderate', 'Moderate NPDR'),
        ('severe', 'Severe NPDR'),
        ('proliferative', 'PDR'),
    ]
    
    EYE_CHOICES = [
        ('left', 'Left Eye'),
        ('right', 'Right Eye'),
        ('both', 'Both Eyes'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
    ]

    patient = models.ForeignKey('DiabetesPatient', on_delete=models.CASCADE, related_name='retinopathy_screenings')
    screening_date = models.DateTimeField(default=timezone.now)
    eye = models.CharField(max_length=10, choices=EYE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    ai_diagnosis = models.TextField()
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    follow_up_date = models.DateField(null=True, blank=True)
    ophthalmologist_referral = models.BooleanField(default=False)
    treatment_recommended = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.patient.user.get_full_name()} - {self.screening_date.date()} - {self.severity}"

    class Meta:
        db_table = 'retinopathy_screenings'
        ordering = ['-screening_date']


class FundusImage(models.Model):
    """Model for fundus photograph storage and analysis"""
    EYE_CHOICES = [
        ('left', 'Left Eye'),
        ('right', 'Right Eye'),
    ]
    
    IMAGE_QUALITY_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('acceptable', 'Acceptable'),
        ('poor', 'Poor'),
    ]

    patient = models.ForeignKey('DiabetesPatient', on_delete=models.CASCADE, related_name='fundus_images')
    eye = models.CharField(max_length=10, choices=EYE_CHOICES)
    image_file = models.ImageField(upload_to='fundus_images/')
    image_quality = models.CharField(max_length=20, choices=IMAGE_QUALITY_CHOICES, default='good')
    capture_date = models.DateTimeField(default=timezone.now)
    
    # AI Analysis Results
    ai_processed = models.BooleanField(default=False)
    ai_analysis_date = models.DateTimeField(null=True, blank=True)
    ai_diagnosis = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    detected_features = models.JSONField(default=dict, blank=True)  # Store detected lesions, coordinates, etc.
    annotated_image = models.ImageField(upload_to='annotated_fundus/', null=True, blank=True)
    
    # Clinical Assessment
    clinical_diagnosis = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_fundus_images')
    reviewed_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.patient.user.get_full_name()} - {self.eye} - {self.capture_date.date()}"

    class Meta:
        db_table = 'fundus_images'
        ordering = ['-capture_date']


class AIRetinopathyAnalysis(models.Model):
    """Model for storing detailed AI analysis results"""
    ANALYSIS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    fundus_image = models.OneToOneField('FundusImage', on_delete=models.CASCADE, related_name='ai_analysis')
    analysis_status = models.CharField(max_length=20, choices=ANALYSIS_STATUS_CHOICES, default='pending')
    
    # AI Model Information
    model_version = models.CharField(max_length=50, default='RetinaScan-v3.2')
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    # Detection Results
    microaneurysms_detected = models.IntegerField(default=0)
    hemorrhages_detected = models.IntegerField(default=0)
    hard_exudates_detected = models.IntegerField(default=0)
    soft_exudates_detected = models.IntegerField(default=0)
    neovascularization_detected = models.BooleanField(default=False)
    
    # Risk Scoring
    overall_risk_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    progression_risk = models.CharField(max_length=10, choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')])
    
    # Recommendations
    recommended_follow_up_months = models.IntegerField(default=12)
    ophthalmology_referral_recommended = models.BooleanField(default=False)
    urgent_referral_required = models.BooleanField(default=False)
    
    # Additional Analysis Data
    analysis_data = models.JSONField(default=dict, blank=True)  # Store detailed analysis results
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Analysis - {self.fundus_image.patient.patient.user.get_full_name()} - {self.created_at.date()}"

    class Meta:
        db_table = 'ai_retinopathy_analysis'
        ordering = ['-created_at']
