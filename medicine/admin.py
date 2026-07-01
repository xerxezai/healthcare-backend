from django.contrib import admin
from .models import (
    Patient, Doctor, VitalSigns, Appointment, Prescription,
    LabTest, EmergencyCase, TreatmentPlan, MedicalRecord,
    PatientReport, SOAPNote, ProtocolSummarizer, ContractRedlining,
    PhysicianAssistant, AIBookingAssistant, InsurancePolicyCopilot,
    HospitalCSRAssistant, MedicalResearchReview, BackOfficeAutomation,
    ClinicalHistorySearch, DiabetesPatient, BloodGlucoseReading,
    HbA1cRecord, DiabetesMedication, DiabetesComplicationScreening,
    DiabetesEducationSession, DiabetesEmergencyEvent, DiabetesGoal
)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'user', 'date_of_birth', 'gender', 'blood_type', 'phone', 'created_at']
    list_filter = ['gender', 'blood_type', 'created_at']
    search_fields = ['patient_id', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['patient_id', 'age', 'bmi', 'created_at', 'updated_at']

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'specialization', 'qualification', 'years_experience', 'is_available_emergency']
    list_filter = ['specialization', 'qualification', 'is_available_emergency']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'temperature', 'blood_pressure', 'heart_rate', 'recorded_by', 'recorded_at']
    list_filter = ['recorded_at']
    search_fields = ['patient__patient_id', 'patient__user__first_name', 'patient__user__last_name']
    readonly_fields = ['bmi', 'recorded_at']

    def blood_pressure(self, obj):
        if obj.blood_pressure_systolic and obj.blood_pressure_diastolic:
            return f"{obj.blood_pressure_systolic}/{obj.blood_pressure_diastolic}"
        return "-"
    blood_pressure.short_description = "Blood Pressure"

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_type', 'scheduled_datetime', 'status', 'priority']
    list_filter = ['appointment_type', 'status', 'priority', 'scheduled_datetime', 'is_emergency']
    search_fields = ['appointment_id', 'patient__patient_id', 'doctor__user__first_name', 'doctor__user__last_name']
    readonly_fields = ['appointment_id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_datetime'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_id', 'patient', 'doctor', 'medication_name', 'dosage', 'frequency', 'dispensed']
    list_filter = ['medication_type', 'frequency', 'dispensed', 'created_at']
    search_fields = ['prescription_id', 'medication_name', 'patient__patient_id']
    readonly_fields = ['prescription_id', 'created_at']

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ['test_id', 'patient', 'test_name', 'test_category', 'status', 'is_abnormal', 'is_critical', 'ordered_date']
    list_filter = ['test_category', 'status', 'is_abnormal', 'is_critical', 'ordered_date']
    search_fields = ['test_id', 'test_name', 'patient__patient_id']
    readonly_fields = ['test_id', 'ordered_date']

@admin.register(EmergencyCase)
class EmergencyCaseAdmin(admin.ModelAdmin):
    list_display = ['case_id', 'patient', 'triage_level', 'arrival_mode', 'disposition', 'is_trauma', 'is_critical', 'arrival_datetime']
    list_filter = ['triage_level', 'arrival_mode', 'disposition', 'is_trauma', 'is_critical', 'arrival_datetime']
    search_fields = ['case_id', 'patient__patient_id', 'chief_complaint']
    readonly_fields = ['case_id', 'arrival_datetime', 'created_at', 'updated_at']
    date_hierarchy = 'arrival_datetime'

@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'patient', 'created_by', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'plan_type', 'start_date']
    search_fields = ['plan_id', 'patient__patient_id', 'primary_diagnosis', 'treatment_goals']
    readonly_fields = ['plan_id', 'created_at', 'updated_at']

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['record_id', 'patient', 'created_by', 'record_type', 'subject', 'created_at']
    list_filter = ['record_type', 'created_at', 'is_reviewed']
    search_fields = ['record_id', 'patient__patient_id', 'subject', 'assessment']
    readonly_fields = ['record_id', 'created_at', 'updated_at']

# New Feature Admin Classes

@admin.register(PatientReport)
class PatientReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'patient', 'generated_by', 'report_type', 'status', 'title', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['report_id', 'title', 'patient__patient_id']
    readonly_fields = ['report_id', 'created_at', 'updated_at']

@admin.register(SOAPNote)
class SOAPNoteAdmin(admin.ModelAdmin):
    list_display = ['note_id', 'patient', 'created_by', 'appointment', 'chief_complaint', 'is_template', 'created_at']
    list_filter = ['is_template', 'created_at']
    search_fields = ['note_id', 'patient__patient_id', 'chief_complaint']
    readonly_fields = ['note_id', 'created_at', 'updated_at']

@admin.register(ProtocolSummarizer)
class ProtocolSummarizerAdmin(admin.ModelAdmin):
    list_display = ['protocol_id', 'title', 'protocol_type', 'medical_condition', 'specialty', 'is_active', 'views_count']
    list_filter = ['protocol_type', 'specialty', 'is_active', 'effective_date']
    search_fields = ['protocol_id', 'title', 'medical_condition']
    readonly_fields = ['protocol_id', 'views_count', 'downloads_count', 'created_at', 'updated_at']

@admin.register(ContractRedlining)
class ContractRedliningAdmin(admin.ModelAdmin):
    list_display = ['contract_id', 'title', 'contract_type', 'status', 'counterparty_name', 'contract_value', 'created_by']
    list_filter = ['contract_type', 'status', 'created_at']
    search_fields = ['contract_id', 'title', 'counterparty_name']
    readonly_fields = ['contract_id', 'created_at', 'updated_at']

@admin.register(PhysicianAssistant)
class PhysicianAssistantAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'patient', 'doctor', 'session_type', 'chief_complaint', 'rating', 'created_at']
    list_filter = ['session_type', 'rating', 'was_helpful', 'created_at']
    search_fields = ['session_id', 'patient__patient_id', 'chief_complaint']
    readonly_fields = ['session_id', 'created_at', 'updated_at']

@admin.register(AIBookingAssistant)
class AIBookingAssistantAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'patient', 'status', 'communication_channel', 'urgency_level', 'session_start']
    list_filter = ['status', 'communication_channel', 'urgency_level', 'session_start']
    search_fields = ['booking_id', 'patient__patient_id']
    readonly_fields = ['booking_id', 'session_start', 'created_at', 'updated_at']

@admin.register(InsurancePolicyCopilot)
class InsurancePolicyCopilotAdmin(admin.ModelAdmin):
    list_display = ['policy_id', 'patient', 'insurance_provider', 'policy_type', 'status', 'premium_amount', 'coverage_start_date']
    list_filter = ['policy_type', 'status', 'insurance_provider', 'coverage_start_date']
    search_fields = ['policy_id', 'policy_number', 'patient__patient_id', 'insurance_provider']
    readonly_fields = ['policy_id', 'created_at', 'updated_at']

@admin.register(HospitalCSRAssistant)
class HospitalCSRAssistantAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'patient', 'inquiry_type', 'priority', 'resolution_status', 'caller_name', 'created_at']
    list_filter = ['inquiry_type', 'priority', 'resolution_status', 'created_at']
    search_fields = ['ticket_id', 'caller_name', 'caller_phone', 'subject']
    readonly_fields = ['ticket_id', 'created_at', 'updated_at']

@admin.register(MedicalResearchReview)
class MedicalResearchReviewAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'title', 'research_type', 'journal', 'publication_date', 'quality_rating', 'is_recommended']
    list_filter = ['research_type', 'quality_rating', 'evidence_level', 'is_recommended', 'publication_date']
    search_fields = ['review_id', 'title', 'authors', 'journal', 'doi']
    readonly_fields = ['review_id', 'views_count', 'citations_count', 'bookmarks_count', 'created_at', 'updated_at']

@admin.register(BackOfficeAutomation)
class BackOfficeAutomationAdmin(admin.ModelAdmin):
    list_display = ['automation_id', 'task_name', 'task_type', 'status', 'frequency', 'is_active', 'success_count', 'failure_count']
    list_filter = ['task_type', 'status', 'frequency', 'is_active', 'created_at']
    search_fields = ['automation_id', 'task_name']
    readonly_fields = ['automation_id', 'execution_count', 'success_count', 'failure_count', 'created_at', 'updated_at']

@admin.register(ClinicalHistorySearch)
class ClinicalHistorySearchAdmin(admin.ModelAdmin):
    list_display = ['search_id', 'searched_by', 'patient', 'search_type', 'results_count', 'user_satisfaction', 'created_at']
    list_filter = ['search_type', 'user_satisfaction', 'created_at']
    search_fields = ['search_id', 'search_query', 'patient__patient_id']
    readonly_fields = ['search_id', 'results_count', 'search_time_ms', 'created_at']


# ============================================================================
# DIABETES MANAGEMENT ADMIN
# ============================================================================

@admin.register(DiabetesPatient)
class DiabetesPatientAdmin(admin.ModelAdmin):
    list_display = ['patient', 'diabetes_type', 'diagnosis_date', 'current_hba1c', 'hba1c_target', 'insulin_regimen']
    list_filter = ['diabetes_type', 'insulin_regimen', 'monitoring_method', 'smoking_status']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'patient__patient_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'diabetes_type', 'diagnosis_date')
        }),
        ('Clinical Management', {
            'fields': ('hba1c_target', 'current_hba1c', 'target_glucose_min', 'target_glucose_max')
        }),
        ('Insulin Therapy', {
            'fields': ('insulin_regimen', 'total_daily_dose', 'carb_ratio', 'correction_factor')
        }),
        ('Monitoring', {
            'fields': ('monitoring_method',)
        }),
        ('Complications', {
            'fields': ('has_retinopathy', 'has_nephropathy', 'has_neuropathy', 'has_cardiovascular_disease')
        }),
        ('Lifestyle', {
            'fields': ('exercise_frequency', 'smoking_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(BloodGlucoseReading)
class BloodGlucoseReadingAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'glucose_value', 'reading_type', 'reading_datetime', 'is_hypoglycemic', 'is_hyperglycemic']
    list_filter = ['reading_type', 'is_hypoglycemic', 'is_hyperglycemic', 'reading_datetime']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name']
    readonly_fields = ['is_hypoglycemic', 'is_hyperglycemic', 'created_at']
    date_hierarchy = 'reading_datetime'


@admin.register(HbA1cRecord)
class HbA1cRecordAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'hba1c_value', 'test_date', 'is_at_target', 'change_from_previous', 'ordered_by']
    list_filter = ['is_at_target', 'test_date']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name', 'lab_name']
    readonly_fields = ['is_at_target', 'change_from_previous', 'created_at']
    date_hierarchy = 'test_date'


@admin.register(DiabetesMedication)
class DiabetesMedicationAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'medication_name', 'medication_type', 'dosage', 'is_active', 'prescribed_by']
    list_filter = ['medication_type', 'is_active', 'start_date']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name', 'medication_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(DiabetesComplicationScreening)
class DiabetesComplicationScreeningAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'screening_type', 'result', 'screening_date', 'next_screening_date', 'performed_by']
    list_filter = ['screening_type', 'result', 'screening_date']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'screening_date'


@admin.register(DiabetesEducationSession)
class DiabetesEducationSessionAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'education_type', 'session_date', 'duration_minutes', 'patient_understanding_level', 'follow_up_needed']
    list_filter = ['education_type', 'follow_up_needed', 'session_date']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'session_date'


@admin.register(DiabetesEmergencyEvent)
class DiabetesEmergencyEventAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'event_type', 'severity', 'event_datetime', 'hospital_admission', 'glucose_level']
    list_filter = ['event_type', 'severity', 'hospital_admission', 'event_datetime']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'event_datetime'


@admin.register(DiabetesGoal)
class DiabetesGoalAdmin(admin.ModelAdmin):
    list_display = ['diabetes_patient', 'title', 'goal_type', 'status', 'progress_percentage', 'target_date']
    list_filter = ['goal_type', 'status', 'target_date']
    search_fields = ['diabetes_patient__patient__user__first_name', 'diabetes_patient__patient__user__last_name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'target_date'


# ========================================
# S3-INTEGRATED ADMIN CLASSES
# ========================================

from .models import (
    MedicalInstitution, MedicinePatient, Consultation,
    LabResult, MedicineAuditLog, DoctorWorkspace
)

@admin.register(MedicalInstitution)
class MedicalInstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'license_number', 'storage_quota_gb', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'license_number', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(MedicinePatient)
class MedicinePatientAdmin(admin.ModelAdmin):
    list_display = ['patient_code', 'full_name', 'age', 'gender', 'institution', 'is_active', 'created_at']
    list_filter = ['gender', 'blood_type', 'institution', 'is_active', 'created_at']
    search_fields = ['patient_code', 'first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['id', 'age', 'bmi', 'created_at', 'updated_at']

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'consultation_type', 'consultation_date', 'status', 'duration_minutes']
    list_filter = ['consultation_type', 'status', 'consultation_date']
    search_fields = ['patient__patient_code', 'patient__first_name', 'patient__last_name', 'doctor__username']
    readonly_fields = ['id', 's3_notes_key', 'blood_pressure', 'created_at', 'updated_at']

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ['patient', 'test_name', 'test_category', 'lab_facility', 'ordered_date', 'result_date', 'status']
    list_filter = ['test_category', 'status', 'has_abnormal_values', 'has_critical_values', 'ordered_date']
    search_fields = ['patient__patient_code', 'test_name', 'lab_facility']
    readonly_fields = ['id', 's3_result_key', 'created_at', 'updated_at']

@admin.register(MedicineAuditLog)
class MedicineAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'resource_type', 'user', 'institution', 'timestamp']
    list_filter = ['action', 'resource_type', 'institution', 'timestamp']
    search_fields = ['resource_id', 'user__username', 'user_ip']
    readonly_fields = ['id', 'timestamp']

@admin.register(DoctorWorkspace)
class DoctorWorkspaceAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'institution', 'total_consultations', 'total_patients_treated', 'is_active', 'last_activity']
    list_filter = ['is_active', 'institution', 'last_activity']
    search_fields = ['doctor__username', 'doctor__first_name', 'doctor__last_name']
    readonly_fields = ['id', 's3_workspace_prefix', 'total_consultations', 'total_patients_treated', 'total_treatment_plans_created', 'created_at', 'updated_at']
