from django.contrib import admin
from .models import (
    Patient, Dentist, DentalHistory, Appointment, Treatment,
    DentalXray, PeriodontalChart, DentalAIAnalysis, Prescription,
    DentalEmergency, TreatmentPlan
)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'user', 'phone', 'created_at']
    search_fields = ['patient_id', 'user__first_name', 'user__last_name', 'phone']
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ['patient_id', 'created_at', 'updated_at']

@admin.register(Dentist)
class DentistAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'specialization', 'years_experience', 'is_available', 'rating']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']
    list_filter = ['specialization', 'is_available', 'years_experience']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DentalHistory)
class DentalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'brushing_frequency', 'smoking', 'dental_anxiety_level', 'updated_at']
    search_fields = ['patient__user__first_name', 'patient__user__last_name']
    list_filter = ['smoking', 'teeth_grinding', 'previous_orthodontics']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'dentist', 'appointment_date', 'appointment_type', 'status']
    search_fields = ['appointment_id', 'patient__user__first_name', 'patient__user__last_name']
    list_filter = ['appointment_type', 'status', 'appointment_date']
    readonly_fields = ['appointment_id', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['treatment_id', 'patient', 'dentist', 'treatment_name', 'status', 'start_date', 'cost']
    search_fields = ['treatment_id', 'treatment_name', 'patient__user__first_name']
    list_filter = ['status', 'start_date', 'treatment_code']
    readonly_fields = ['treatment_id', 'created_at', 'updated_at']

@admin.register(DentalXray)
class DentalXrayAdmin(admin.ModelAdmin):
    list_display = ['xray_id', 'patient', 'dentist', 'xray_type', 'taken_date', 'image_quality']
    search_fields = ['xray_id', 'patient__user__first_name', 'patient__user__last_name']
    list_filter = ['xray_type', 'image_quality', 'taken_date']
    readonly_fields = ['xray_id', 'created_at', 'updated_at']

@admin.register(PeriodontalChart)
class PeriodontalChartAdmin(admin.ModelAdmin):
    list_display = ['chart_id', 'patient', 'dentist', 'chart_date', 'overall_periodontal_status']
    search_fields = ['chart_id', 'patient__user__first_name', 'patient__user__last_name']
    list_filter = ['overall_periodontal_status', 'chart_date']
    readonly_fields = ['chart_id', 'created_at', 'updated_at']

@admin.register(DentalAIAnalysis)
class DentalAIAnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_id', 'patient', 'dentist', 'analysis_type', 'confidence_level', 'risk_score', 'approved_by_dentist']
    search_fields = ['analysis_id', 'patient__user__first_name', 'patient__user__last_name']
    list_filter = ['analysis_type', 'confidence_level', 'approved_by_dentist', 'created_at']
    readonly_fields = ['analysis_id', 'ai_model_version', 'processing_time', 'created_at', 'updated_at']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_id', 'patient', 'dentist', 'medication_name', 'medication_type', 'prescribed_date', 'is_active']
    search_fields = ['prescription_id', 'medication_name', 'patient__user__first_name']
    list_filter = ['medication_type', 'is_active', 'prescribed_date']
    readonly_fields = ['prescription_id', 'created_at', 'updated_at']

@admin.register(DentalEmergency)
class DentalEmergencyAdmin(admin.ModelAdmin):
    list_display = ['emergency_id', 'patient', 'emergency_type', 'severity', 'pain_level', 'is_resolved', 'created_at']
    search_fields = ['emergency_id', 'patient__user__first_name', 'patient__user__last_name']
    list_filter = ['emergency_type', 'severity', 'is_resolved', 'created_at']
    readonly_fields = ['emergency_id', 'created_at', 'updated_at']

@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'patient', 'primary_dentist', 'plan_name', 'status', 'patient_approved', 'total_estimated_cost']
    search_fields = ['plan_id', 'plan_name', 'patient__user__first_name']
    list_filter = ['status', 'patient_approved', 'created_at']
    readonly_fields = ['plan_id', 'created_at', 'updated_at']
