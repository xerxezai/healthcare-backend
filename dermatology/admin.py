from django.contrib import admin
from .models import (
    DermatologyDepartment, SkinCondition, Patient, DermatologyConsultation,
    DiagnosticProcedure, SkinPhoto, TreatmentPlan, TreatmentOutcome, AIAnalysis
)


@admin.register(DermatologyDepartment)
class DermatologyDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'head_doctor', 'location', 'emergency_services', 'is_active', 'created_at']
    list_filter = ['emergency_services', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'head_doctor')
        }),
        ('Contact Details', {
            'fields': ('location', 'contact_phone', 'contact_email', 'operating_hours')
        }),
        ('Settings', {
            'fields': ('emergency_services', 'is_active')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SkinCondition)
class SkinConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'icd10_code', 'category', 'severity_level', 'is_contagious', 'requires_biopsy', 'is_active']
    list_filter = ['category', 'severity_level', 'is_contagious', 'requires_biopsy', 'is_active', 'created_at']
    search_fields = ['name', 'icd10_code', 'description', 'symptoms']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'icd10_code', 'category', 'severity_level')
        }),
        ('Medical Details', {
            'fields': ('description', 'symptoms', 'risk_factors', 'treatment_guidelines')
        }),
        ('Characteristics', {
            'fields': ('is_contagious', 'requires_biopsy', 'typical_duration', 'recurrence_rate')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'medical_record_number', 'skin_type', 'smoking_status', 'previous_skin_cancer', 'created_at']
    list_filter = ['skin_type', 'smoking_status', 'previous_skin_cancer', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'medical_record_number', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Patient Name'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'medical_record_number', 'skin_type')
        }),
        ('Medical History', {
            'fields': ('family_history', 'known_allergies', 'current_medications', 'sun_exposure_history')
        }),
        ('Personal Information', {
            'fields': ('occupation', 'smoking_status', 'alcohol_consumption', 'previous_skin_cancer')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Insurance', {
            'fields': ('insurance_provider', 'insurance_policy_number')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DermatologyConsultation)
class DermatologyConsultationAdmin(admin.ModelAdmin):
    list_display = ['consultation_number', 'get_patient_name', 'dermatologist', 'consultation_type', 'scheduled_date', 'status', 'priority']
    list_filter = ['consultation_type', 'status', 'priority', 'department', 'scheduled_date', 'created_at']
    search_fields = ['consultation_number', 'patient__user__first_name', 'patient__user__last_name', 'chief_complaint']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Consultation Details', {
            'fields': ('consultation_number', 'patient', 'dermatologist', 'department')
        }),
        ('Scheduling', {
            'fields': ('consultation_type', 'scheduled_date', 'actual_start_time', 'actual_end_time', 'status', 'priority')
        }),
        ('Clinical Information', {
            'fields': ('chief_complaint', 'history_of_present_illness', 'review_of_systems', 'physical_examination')
        }),
        ('Assessment & Plan', {
            'fields': ('assessment', 'plan', 'follow_up_instructions', 'next_appointment_recommended')
        }),
        ('Notes', {
            'fields': ('consultation_notes',)
        }),
        ('System Information', {
            'fields': ('created_by', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DiagnosticProcedure)
class DiagnosticProcedureAdmin(admin.ModelAdmin):
    list_display = ['procedure_number', 'procedure_name', 'procedure_type', 'get_patient_name', 'procedure_date', 'status']
    list_filter = ['procedure_type', 'status', 'procedure_date', 'created_at']
    search_fields = ['procedure_number', 'procedure_name', 'indication', 'consultation__patient__user__first_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'procedure_date'
    
    def get_patient_name(self, obj):
        return obj.consultation.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Procedure Details', {
            'fields': ('procedure_number', 'consultation', 'procedure_type', 'procedure_name')
        }),
        ('Clinical Information', {
            'fields': ('indication', 'anatomical_location', 'procedure_date', 'performed_by', 'status')
        }),
        ('Procedure Details', {
            'fields': ('procedure_details', 'findings', 'complications', 'post_procedure_care')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SkinPhoto)
class SkinPhotoAdmin(admin.ModelAdmin):
    list_display = ['get_patient_name', 'photo_type', 'anatomical_region', 'taken_at', 'taken_by', 'consent_obtained']
    list_filter = ['photo_type', 'anatomical_region', 'consent_obtained', 'is_before_treatment', 'is_after_treatment', 'taken_at']
    search_fields = ['consultation__patient__user__first_name', 'consultation__patient__user__last_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'taken_at'
    
    def get_patient_name(self, obj):
        return obj.consultation.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('consultation', 'photo_type', 'anatomical_region', 'specific_location')
        }),
        ('Image Files', {
            'fields': ('image_file', 'thumbnail', 'description')
        }),
        ('Technical Details', {
            'fields': ('magnification', 'lighting_conditions', 'camera_settings', 'taken_by', 'taken_at')
        }),
        ('Treatment Documentation', {
            'fields': ('is_before_treatment', 'is_after_treatment', 'treatment_day')
        }),
        ('Permissions', {
            'fields': ('consent_obtained', 'research_use_permitted', 'teaching_use_permitted')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['treatment_name', 'get_patient_name', 'diagnosed_condition', 'treatment_category', 'status', 'start_date', 'prescribed_by']
    list_filter = ['treatment_category', 'status', 'diagnosed_condition', 'start_date', 'created_at']
    search_fields = ['treatment_name', 'medication_name', 'consultation__patient__user__first_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    def get_patient_name(self, obj):
        return obj.consultation.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Treatment Information', {
            'fields': ('consultation', 'diagnosed_condition', 'treatment_category', 'treatment_name')
        }),
        ('Treatment Details', {
            'fields': ('treatment_description', 'medication_name', 'dosage', 'frequency', 'duration')
        }),
        ('Instructions', {
            'fields': ('application_instructions', 'precautions', 'expected_outcomes', 'potential_side_effects')
        }),
        ('Timeline', {
            'fields': ('start_date', 'expected_end_date', 'actual_end_date', 'status')
        }),
        ('Monitoring', {
            'fields': ('effectiveness_rating', 'patient_compliance', 'treatment_notes', 'prescribed_by')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TreatmentOutcome)
class TreatmentOutcomeAdmin(admin.ModelAdmin):
    list_display = ['get_treatment_name', 'get_patient_name', 'assessment_date', 'outcome_status', 'improvement_percentage', 'assessed_by']
    list_filter = ['outcome_status', 'assessment_date', 'created_at']
    search_fields = ['treatment_plan__treatment_name', 'treatment_plan__consultation__patient__user__first_name', 'clinical_notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'assessment_date'
    
    def get_treatment_name(self, obj):
        return obj.treatment_plan.treatment_name
    get_treatment_name.short_description = 'Treatment'
    
    def get_patient_name(self, obj):
        return obj.treatment_plan.consultation.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Assessment Information', {
            'fields': ('treatment_plan', 'assessment_date', 'assessed_by')
        }),
        ('Outcome Details', {
            'fields': ('outcome_status', 'improvement_percentage', 'symptom_severity_score', 'patient_satisfaction')
        }),
        ('Clinical Notes', {
            'fields': ('side_effects_reported', 'quality_of_life_impact', 'clinical_notes')
        }),
        ('Measurements', {
            'fields': ('objective_measurements',)
        }),
        ('Follow-up', {
            'fields': ('next_assessment_date', 'treatment_modifications')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ['get_patient_name', 'analysis_type', 'confidence_level', 'requires_biopsy', 'validated_by_doctor', 'analysis_date']
    list_filter = ['analysis_type', 'confidence_level', 'requires_biopsy', 'validated_by_doctor', 'urgency_level', 'analysis_date']
    search_fields = ['skin_photo__consultation__patient__user__first_name', 'risk_assessment', 'recommended_actions']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'analysis_date'
    
    def get_patient_name(self, obj):
        return obj.skin_photo.consultation.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('skin_photo', 'analysis_type', 'ai_model_version', 'analysis_date')
        }),
        ('Confidence & Risk', {
            'fields': ('confidence_level', 'confidence_score', 'urgency_level', 'requires_biopsy')
        }),
        ('Findings', {
            'fields': ('primary_findings', 'secondary_findings', 'differential_diagnosis')
        }),
        ('Analysis Details', {
            'fields': ('feature_analysis', 'lesion_measurements', 'color_analysis', 'texture_metrics')
        }),
        ('ABCDE Assessment', {
            'fields': ('asymmetry_score', 'border_irregularity', 'color_variation', 'diameter_mm', 'evolution_detected')
        }),
        ('Recommendations', {
            'fields': ('risk_assessment', 'recommended_actions')
        }),
        ('Doctor Validation', {
            'fields': ('validated_by_doctor', 'doctor_agreement', 'doctor_notes')
        }),
        ('Performance', {
            'fields': ('processing_time_seconds',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
