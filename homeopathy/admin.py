from django.contrib import admin
from .models import HomeopathyPatient, HomeopathyRemedy, HomeopathyDiagnosis, HomeopathyRemedySuggestion

@admin.register(HomeopathyPatient)
class HomeopathyPatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'gender', 'constitution', 'created_by', 'created_at']
    list_filter = ['gender', 'constitution', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Patient Information', {
            'fields': ('name', 'age', 'gender', 'phone', 'email')
        }),
        ('Constitutional Info', {
            'fields': ('constitution',)
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(HomeopathyRemedy)
class HomeopathyRemedyAdmin(admin.ModelAdmin):
    list_display = ['name', 'latin_name', 'miasm', 'created_at']
    list_filter = ['miasm', 'created_at']
    search_fields = ['name', 'latin_name', 'common_name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['antidotes', 'complementary']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'latin_name', 'common_name')
        }),
        ('Characteristics', {
            'fields': ('keynotes', 'mental_symptoms', 'physical_symptoms', 'indications')
        }),
        ('Constitutional & Miasmatic', {
            'fields': ('miasm', 'constitution_affinity')
        }),
        ('Prescribing Information', {
            'fields': ('common_potencies', 'dosage_notes')
        }),
        ('Relationships', {
            'fields': ('antidotes', 'complementary')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(HomeopathyDiagnosis)
class HomeopathyDiagnosisAdmin(admin.ModelAdmin):
    list_display = ['patient', 'practitioner', 'status', 'ai_confidence', 'created_at']
    list_filter = ['status', 'miasm', 'suggested_constitution', 'created_at']
    search_fields = ['patient__name', 'practitioner__username', 'primary_symptoms']
    readonly_fields = ['created_at', 'updated_at', 'analyzed_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'practitioner', 'status')
        }),
        ('Chief Complaints', {
            'fields': ('primary_symptoms', 'duration', 'onset', 'severity')
        }),
        ('Mental & Emotional', {
            'fields': ('mental_state', 'emotional_pattern', 'fears', 'anxieties', 'mood')
        }),
        ('Physical Generals', {
            'fields': ('appetite', 'thirst', 'sleep', 'dreams', 'thermals', 'perspiration')
        }),
        ('Modalities', {
            'fields': ('better_by', 'worse_by', 'time_aggravation')
        }),
        ('Constitutional', {
            'fields': ('energy', 'circulation', 'digestion', 'elimination')
        }),
        ('Miasmatic Analysis', {
            'fields': ('miasm', 'family_history', 'past_illness')
        }),
        ('Additional Information', {
            'fields': ('lifestyle', 'environment', 'stress_factors', 'previous_treatments')
        }),
        ('AI Analysis Results', {
            'fields': ('ai_confidence', 'suggested_constitution', 'suggested_miasm', 
                      'mental_emotional_score', 'physical_score', 'modality_score'),
            'classes': ['collapse']
        }),
        ('Treatment Recommendations', {
            'fields': ('estimated_duration', 'suggested_potency', 'suggested_frequency', 
                      'follow_up_recommendations'),
            'classes': ['collapse']
        }),
        ('System Info', {
            'fields': ('analyzed_at', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

@admin.register(HomeopathyRemedySuggestion)
class HomeopathyRemedySuggestionAdmin(admin.ModelAdmin):
    list_display = ['diagnosis', 'remedy', 'rank', 'confidence_score', 'suggested_potency']
    list_filter = ['rank', 'suggested_potency', 'created_at']
    search_fields = ['diagnosis__patient__name', 'remedy__name']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('diagnosis', 'remedy', 'rank')
        }),
        ('AI Scoring', {
            'fields': ('confidence_score', 'keynote_match_score', 'mental_match_score', 
                      'physical_match_score', 'constitutional_match_score')
        }),
        ('Prescription Suggestion', {
            'fields': ('suggested_potency', 'suggested_frequency', 'duration')
        }),
        ('AI Reasoning', {
            'fields': ('ai_reasoning', 'matching_symptoms')
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ['collapse']
        }),
    )
