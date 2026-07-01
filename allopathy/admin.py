from django.contrib import admin
from .models import (
    AllopathyHospital, AllopathyPatientS3, AllopathyFile, 
    AllopathyAnalysis, AllopathyMedicalRecord, AllopathyTreatmentPlan
)

@admin.register(AllopathyHospital)
class AllopathyHospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'hospital_type', 'chief_physician', 'city', 'status', 'created_at']
    list_filter = ['hospital_type', 'status', 'city']
    search_fields = ['name', 'chief_physician', 'license_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AllopathyPatientS3)
class AllopathyPatientS3Admin(admin.ModelAdmin):
    list_display = ['patient_id', 'first_name', 'last_name', 'age', 'gender', 'admission_type', 'status']
    list_filter = ['gender', 'admission_type', 'status', 'blood_group']
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AllopathyFile)
class AllopathyFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'category', 'patient_name', 'file_size', 'status', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['filename', 'original_name', 'patient_name']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'file_hash']

@admin.register(AllopathyAnalysis)
class AllopathyAnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_type', 'patient_name', 'confidence_score', 'status', 'created_at']
    list_filter = ['analysis_type', 'status', 'created_at']
    search_fields = ['patient_name', 'analysis_type']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AllopathyMedicalRecord)
class AllopathyMedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'chief_complaint', 'attending_physician', 'admission_date', 'status']
    list_filter = ['status', 'admission_date', 'discharge_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'chief_complaint']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AllopathyTreatmentPlan)
class AllopathyTreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['patient', 'diagnosis', 'treatment_plan', 'prescribed_by', 'plan_date', 'status']
    list_filter = ['status', 'plan_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at']
