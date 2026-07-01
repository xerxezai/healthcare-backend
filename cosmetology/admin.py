from django.contrib import admin
from .models import (
    CosmetologyClient, CosmetologyService, CosmetologyProduct, 
    CosmetologyAppointment, CosmetologyTreatmentPlan, CosmetologyConsultation,
    CosmetologyProgress, TreatmentPlanService, TreatmentPlanProduct,
    # Cosmetic Gynecology Models
    CosmeticGynecologyClient, CosmeticGynecologyTreatment, CosmeticGynecologyConsultation,
    CosmeticGynecologyTreatmentPlan, CosmeticGynecologyProgress
)

@admin.register(CosmetologyClient)
class CosmetologyClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'gender', 'skin_type', 'hair_type', 'created_by', 'created_at']
    list_filter = ['gender', 'skin_type', 'hair_type', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'age', 'gender', 'phone', 'email', 'address')
        }),
        ('Beauty Profile', {
            'fields': ('skin_type', 'hair_type', 'allergies', 'skin_concerns', 'hair_concerns')
        }),
        ('Preferences', {
            'fields': ('preferred_brands', 'budget_range', 'lifestyle_notes')
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(CosmetologyService)
class CosmetologyServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'duration', 'price', 'requires_consultation', 'is_active']
    list_filter = ['category', 'requires_consultation', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'is_active')
        }),
        ('Service Details', {
            'fields': ('duration', 'price', 'requires_consultation', 'session_gap_days')
        }),
        ('Requirements & Care', {
            'fields': ('requirements', 'contraindications', 'aftercare_instructions')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(CosmetologyProduct)
class CosmetologyProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'product_type', 'price', 'stock_quantity', 'is_active']
    list_filter = ['product_type', 'brand', 'is_active', 'created_at']
    search_fields = ['name', 'brand', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'brand', 'product_type', 'description', 'is_active')
        }),
        ('Product Details', {
            'fields': ('ingredients', 'benefits', 'skin_types', 'usage_instructions')
        }),
        ('Inventory & Pricing', {
            'fields': ('stock_quantity', 'price', 'cost_price')
        }),
        ('Safety & Compliance', {
            'fields': ('expiry_date', 'batch_number', 'safety_warnings')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(CosmetologyAppointment)
class CosmetologyAppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'service', 'cosmetologist', 'appointment_date', 'status', 'total_amount']
    list_filter = ['status', 'appointment_date', 'service__category']
    search_fields = ['client__name', 'service__name', 'cosmetologist__username']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Appointment Details', {
            'fields': ('client', 'service', 'cosmetologist', 'appointment_date', 'duration', 'status')
        }),
        ('Consultation & Service', {
            'fields': ('consultation_notes', 'service_notes', 'aftercare_given')
        }),
        ('Pricing', {
            'fields': ('service_price', 'additional_charges', 'discount', 'total_amount')
        }),
        ('Follow-up', {
            'fields': ('next_appointment_due', 'follow_up_notes')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

class TreatmentPlanServiceInline(admin.TabularInline):
    model = TreatmentPlanService
    extra = 1

class TreatmentPlanProductInline(admin.TabularInline):
    model = TreatmentPlanProduct
    extra = 1

@admin.register(CosmetologyTreatmentPlan)
class CosmetologyTreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'cosmetologist', 'duration_weeks', 'start_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'duration_weeks']
    search_fields = ['name', 'client__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TreatmentPlanServiceInline, TreatmentPlanProductInline]
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'client', 'cosmetologist', 'description', 'is_active')
        }),
        ('Goals & Timeline', {
            'fields': ('beauty_goals', 'target_concerns', 'duration_weeks', 'start_date', 'end_date')
        }),
        ('Progress & Costs', {
            'fields': ('progress_notes', 'estimated_cost')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(CosmetologyConsultation)
class CosmetologyConsultationAdmin(admin.ModelAdmin):
    list_display = ['client', 'cosmetologist', 'consultation_date', 'consultation_fee']
    list_filter = ['consultation_date', 'cosmetologist']
    search_fields = ['client__name', 'primary_concerns']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'consultation_date'
    fieldsets = (
        ('Consultation Details', {
            'fields': ('client', 'cosmetologist', 'consultation_date', 'consultation_fee')
        }),
        ('Analysis', {
            'fields': ('skin_analysis', 'skin_photos', 'hair_analysis', 'scalp_condition')
        }),
        ('Goals & Concerns', {
            'fields': ('primary_concerns', 'beauty_goals', 'lifestyle_factors')
        }),
        ('Recommendations', {
            'fields': ('immediate_recommendations', 'long_term_plan', 'product_recommendations')
        }),
        ('Follow-up', {
            'fields': ('next_consultation_date',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(CosmetologyProgress)
class CosmetologyProgressAdmin(admin.ModelAdmin):
    list_display = ['client', 'date_recorded', 'client_satisfaction', 'recorded_by']
    list_filter = ['date_recorded', 'client_satisfaction', 'recorded_by']
    search_fields = ['client__name', 'improvements_noted']
    readonly_fields = ['created_at']
    date_hierarchy = 'date_recorded'
    fieldsets = (
        ('Progress Details', {
            'fields': ('client', 'treatment_plan', 'date_recorded', 'recorded_by')
        }),
        ('Measurements & Photos', {
            'fields': ('progress_photos', 'measurements', 'improvements_noted', 'concerns_remaining')
        }),
        ('Client Feedback', {
            'fields': ('client_satisfaction', 'client_feedback')
        }),
        ('Next Steps', {
            'fields': ('recommendations', 'plan_adjustments')
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ['collapse']
        }),
    )


# =============== COSMETIC GYNECOLOGY ADMIN ===============

@admin.register(CosmeticGynecologyClient)
class CosmeticGynecologyClientAdmin(admin.ModelAdmin):
    list_display = ['get_client_name', 'get_age', 'number_of_pregnancies', 'menopause_status', 'concern_severity', 'created_at']
    list_filter = ['menopause_status', 'c_section_history', 'hormonal_therapy', 'previous_treatments', 'created_at']
    search_fields = ['cosmetology_client__name', 'cosmetology_client__email', 'treatment_goals']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_client_name(self, obj):
        return obj.cosmetology_client.name
    get_client_name.short_description = 'Client Name'
    
    def get_age(self, obj):
        return obj.cosmetology_client.age
    get_age.short_description = 'Age'
    
    fieldsets = (
        ('Client Link', {
            'fields': ('cosmetology_client',)
        }),
        ('Reproductive History', {
            'fields': (
                'age_at_first_pregnancy', 'number_of_pregnancies', 'number_of_deliveries',
                'c_section_history', 'menopause_status', 'hormonal_therapy'
            )
        }),
        ('Concerns & Goals', {
            'fields': ('primary_concerns', 'concern_severity', 'treatment_goals', 'lifestyle_factors')
        }),
        ('Medical History', {
            'fields': (
                'gynecological_conditions', 'current_medications', 
                'previous_treatments', 'treatment_satisfaction'
            )
        }),
        ('AI Analysis', {
            'fields': ('ai_risk_assessment', 'ai_treatment_recommendations', 'ai_recovery_prediction'),
            'classes': ['collapse']
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(CosmeticGynecologyTreatment)
class CosmeticGynecologyTreatmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'technology_used', 'duration_minutes', 'sessions_required', 'success_rate', 'price_per_session', 'is_active']
    list_filter = ['category', 'technology_used', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'indications']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'technology_used', 'description', 'is_active')
        }),
        ('Clinical Information', {
            'fields': ('indications', 'contraindications', 'success_rate', 'side_effects')
        }),
        ('Treatment Protocol', {
            'fields': (
                'duration_minutes', 'sessions_required', 'interval_between_sessions',
                'downtime_days', 'recovery_instructions', 'follow_up_schedule'
            )
        }),
        ('Pricing', {
            'fields': ('price_per_session', 'package_pricing')
        }),
        ('AI Optimization', {
            'fields': ('ai_suitability_criteria', 'ai_outcome_predictors'),
            'classes': ['collapse']
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ['collapse']
        }),
    )


@admin.register(CosmeticGynecologyConsultation)
class CosmeticGynecologyConsultationAdmin(admin.ModelAdmin):
    list_display = ['get_client_name', 'consultation_date', 'status', 'ai_analysis_complete', 'ai_risk_score', 'created_at']
    list_filter = ['status', 'ai_analysis_complete', 'consultation_date', 'created_at']
    search_fields = ['client__cosmetology_client__name', 'chief_complaints', 'doctor_notes']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_client_name(self, obj):
        return obj.client.cosmetology_client.name
    get_client_name.short_description = 'Client Name'
    
    fieldsets = (
        ('Consultation Details', {
            'fields': ('client', 'consultation_date', 'status')
        }),
        ('Assessment', {
            'fields': (
                'chief_complaints', 'physical_examination', 
                'client_expectations', 'psychological_readiness'
            )
        }),
        ('AI Analysis Results', {
            'fields': (
                'ai_analysis_complete', 'ai_risk_score', 'ai_recommended_treatments',
                'ai_treatment_timeline', 'ai_expected_outcomes', 'ai_contraindications'
            ),
            'classes': ['collapse']
        }),
        ('Professional Assessment', {
            'fields': ('doctor_notes', 'recommended_treatment_plan')
        }),
        ('Follow-up', {
            'fields': ('next_consultation', 'consultation_notes')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(CosmeticGynecologyTreatmentPlan)
class CosmeticGynecologyTreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_name', 'get_client_name', 'status', 'start_date', 'total_sessions', 'ai_success_probability', 'total_estimated_cost']
    list_filter = ['status', 'start_date', 'informed_consent', 'created_at']
    search_fields = ['plan_name', 'client__cosmetology_client__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['primary_treatments', 'supporting_treatments']
    
    def get_client_name(self, obj):
        return obj.client.cosmetology_client.name
    get_client_name.short_description = 'Client Name'
    
    fieldsets = (
        ('Plan Overview', {
            'fields': ('client', 'consultation', 'plan_name', 'status')
        }),
        ('Treatment Details', {
            'fields': ('primary_treatments', 'supporting_treatments')
        }),
        ('Timeline & Scheduling', {
            'fields': (
                'start_date', 'estimated_completion', 'total_sessions', 'session_interval_days'
            )
        }),
        ('AI Optimization', {
            'fields': (
                'ai_plan_optimization', 'ai_success_probability', 
                'ai_risk_mitigation', 'ai_personalization_factors'
            ),
            'classes': ['collapse']
        }),
        ('Financial', {
            'fields': ('total_estimated_cost', 'payment_plan', 'insurance_coverage')
        }),
        ('Monitoring', {
            'fields': ('progress_milestones', 'modification_history')
        }),
        ('Consent & Documentation', {
            'fields': ('informed_consent', 'consent_date', 'treatment_agreement')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(CosmeticGynecologyProgress)
class CosmeticGynecologyProgressAdmin(admin.ModelAdmin):
    list_display = ['get_client_name', 'session_number', 'session_date', 'get_treatment_name', 'ai_improvement_score', 'client_satisfaction']
    list_filter = ['session_date', 'treatment_performed', 'follow_up_required', 'created_at']
    search_fields = ['treatment_plan__client__cosmetology_client__name', 'session_notes', 'client_feedback']
    readonly_fields = ['created_at']
    
    def get_client_name(self, obj):
        return obj.treatment_plan.client.cosmetology_client.name
    get_client_name.short_description = 'Client Name'
    
    def get_treatment_name(self, obj):
        return obj.treatment_performed.name
    get_treatment_name.short_description = 'Treatment'
    
    fieldsets = (
        ('Session Details', {
            'fields': ('treatment_plan', 'session_number', 'session_date', 'treatment_performed')
        }),
        ('Session Assessment', {
            'fields': ('session_notes', 'client_comfort_level', 'before_photos', 'after_photos')
        }),
        ('AI Progress Analysis', {
            'fields': (
                'ai_progress_analysis', 'ai_improvement_score', 
                'ai_next_session_recommendations', 'ai_treatment_adjustments'
            ),
            'classes': ['collapse']
        }),
        ('Client Feedback', {
            'fields': ('client_satisfaction', 'client_feedback', 'side_effects_reported')
        }),
        ('Recovery & Next Steps', {
            'fields': (
                'healing_progress', 'recovery_notes', 'next_session_date',
                'homecare_instructions', 'follow_up_required'
            )
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ['collapse']
        }),
    )
