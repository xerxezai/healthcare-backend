from django.contrib import admin
from .models import Patient, MedicalHistory, Appointment, VitalSigns, LabResult

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'full_name', 'date_of_birth', 'gender', 'phone_number', 'primary_physician', 'is_active']
    list_filter = ['gender', 'blood_type', 'is_active', 'created_at']
    search_fields = ['patient_id', 'first_name', 'last_name', 'email', 'phone_number']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['patient_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient_id', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender', 'blood_type')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Personal Information', {
            'fields': ('marital_status', 'occupation')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone')
        }),
        ('Medical Information', {
            'fields': ('primary_physician', 'insurance_provider', 'insurance_policy_number')
        }),
        ('System Information', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'condition', 'diagnosis_date', 'severity', 'is_chronic', 'is_resolved']
    list_filter = ['severity', 'is_chronic', 'is_resolved', 'diagnosis_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'condition']
    date_hierarchy = 'diagnosis_date'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'appointment_type', 'status']
    list_filter = ['status', 'appointment_type', 'appointment_date']
    search_fields = ['appointment_id', 'patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name']
    date_hierarchy = 'appointment_date'
    readonly_fields = ['appointment_id', 'created_at', 'updated_at']

@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'measured_at', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'temperature', 'weight']
    list_filter = ['measured_at']
    search_fields = ['patient__first_name', 'patient__last_name']
    date_hierarchy = 'measured_at'

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ['patient', 'test_name', 'ordered_date', 'status', 'result_status', 'ordered_by']
    list_filter = ['status', 'result_status', 'test_category', 'ordered_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'test_name', 'test_code']
    date_hierarchy = 'ordered_date'
