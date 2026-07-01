"""
Medicine Module Serializers

Comprehensive serializers for medicine data models with S3 integration support.
Handles serialization/deserialization of medical institutions, patients, records,
consultations, treatment plans, and lab results.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

# Import both old and new models for backward compatibility
from .models import (
    # Legacy models
    Patient, Doctor, VitalSigns, Appointment, Prescription, 
    LabTest, EmergencyCase, TreatmentPlan as LegacyTreatmentPlan, MedicalRecord as LegacyMedicalRecord,
    PatientReport, SOAPNote, ProtocolSummarizer, ContractRedlining,
    PhysicianAssistant, AIBookingAssistant, InsurancePolicyCopilot,
    HospitalCSRAssistant, MedicalResearchReview, BackOfficeAutomation,
    ClinicalHistorySearch, DiabetesPatient, BloodGlucoseReading,
    HbA1cRecord, DiabetesMedication, DiabetesComplicationScreening,
    DiabetesEducationSession, DiabetesEmergencyEvent, DiabetesGoal,
    # New S3-integrated models
    MedicalInstitution, MedicinePatient, MedicalRecord,
    Consultation, TreatmentPlan, LabResult, MedicineAuditLog,
    DoctorWorkspace
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'full_name', 'role']

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    bmi = serializers.ReadOnlyField()
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    specialization_display = serializers.CharField(source='get_specialization_display', read_only=True)
    qualification_display = serializers.CharField(source='get_qualification_display', read_only=True)

    class Meta:
        model = Doctor
        fields = '__all__'

class VitalSignsSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = VitalSigns
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    appointment_id = serializers.IntegerField(write_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    medication_type_display = serializers.CharField(source='get_medication_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'

class LabTestSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    ordered_by = DoctorSerializer(read_only=True)
    appointment_id = serializers.IntegerField(write_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    ordered_by_id = serializers.IntegerField(write_only=True)
    test_category_display = serializers.CharField(source='get_test_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LabTest
        fields = '__all__'

class EmergencyCaseSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    attending_physician = DoctorSerializer(read_only=True)
    triage_nurse_name = serializers.CharField(source='triage_nurse.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    attending_physician_id = serializers.IntegerField(write_only=True)
    triage_level_display = serializers.CharField(source='get_triage_level_display', read_only=True)
    arrival_mode_display = serializers.CharField(source='get_arrival_mode_display', read_only=True)
    disposition_display = serializers.CharField(source='get_disposition_display', read_only=True)

    class Meta:
        model = EmergencyCase
        fields = '__all__'

class TreatmentPlanSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    created_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    created_by_id = serializers.IntegerField(write_only=True)
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TreatmentPlan
        fields = '__all__'

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    created_by = DoctorSerializer(read_only=True)
    reviewed_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    created_by_id = serializers.IntegerField(write_only=True)
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = '__all__'

# Dashboard and Analytics Serializers
class PatientSummarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    recent_appointments_count = serializers.SerializerMethodField()
    recent_prescriptions_count = serializers.SerializerMethodField()
    recent_lab_tests_count = serializers.SerializerMethodField()
    last_visit_date = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'patient_id', 'user', 'age', 'gender', 'blood_type', 'phone', 
                 'recent_appointments_count', 'recent_prescriptions_count', 
                 'recent_lab_tests_count', 'last_visit_date']

    def get_recent_appointments_count(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        last_30_days = timezone.now() - timedelta(days=30)
        return obj.appointments.filter(scheduled_datetime__gte=last_30_days).count()

    def get_recent_prescriptions_count(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        last_30_days = timezone.now() - timedelta(days=30)
        return obj.prescriptions.filter(created_at__gte=last_30_days).count()

    def get_recent_lab_tests_count(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        last_30_days = timezone.now() - timedelta(days=30)
        return obj.lab_tests.filter(ordered_date__gte=last_30_days).count()

    def get_last_visit_date(self, obj):
        last_appointment = obj.appointments.filter(status='completed').first()
        return last_appointment.scheduled_datetime if last_appointment else None

class DashboardStatsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_doctors = serializers.IntegerField()
    total_appointments_today = serializers.IntegerField()
    total_emergency_cases_today = serializers.IntegerField()
    pending_lab_tests = serializers.IntegerField()
    active_treatment_plans = serializers.IntegerField()
    appointments_by_type = serializers.DictField()
    emergency_triage_distribution = serializers.DictField()
    recent_patients = PatientSummarySerializer(many=True)
    upcoming_appointments = AppointmentSerializer(many=True)

class AppointmentCalendarSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    title = serializers.SerializerMethodField()
    start = serializers.DateTimeField(source='scheduled_datetime')
    end = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'appointment_id', 'title', 'start', 'end', 'status', 
                 'priority', 'patient_name', 'doctor_name', 'appointment_type']

    def get_title(self, obj):
        return f"{obj.patient.user.get_full_name()} - {obj.get_appointment_type_display()}"

    def get_end(self, obj):
        from datetime import timedelta
        return obj.scheduled_datetime + timedelta(minutes=obj.duration_minutes)

# New Feature Serializers

class PatientReportSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    generated_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    generated_by_id = serializers.IntegerField(write_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PatientReport
        fields = '__all__'

class SOAPNoteSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    created_by = DoctorSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    created_by_id = serializers.IntegerField(write_only=True)
    appointment_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = SOAPNote
        fields = '__all__'

class ProtocolSummarizerSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    protocol_type_display = serializers.CharField(source='get_protocol_type_display', read_only=True)
    created_by_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProtocolSummarizer
        fields = '__all__'

class ContractRedliningSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ContractRedlining
        fields = '__all__'

class PhysicianAssistantSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)

    class Meta:
        model = PhysicianAssistant
        fields = '__all__'

class AIBookingAssistantSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    preferred_doctor = DoctorSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    communication_channel_display = serializers.CharField(source='get_communication_channel_display', read_only=True)

    class Meta:
        model = AIBookingAssistant
        fields = '__all__'

class InsurancePolicyCopilotSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    policy_type_display = serializers.CharField(source='get_policy_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InsurancePolicyCopilot
        fields = '__all__'

class HospitalCSRAssistantSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    escalated_to_name = serializers.CharField(source='escalated_to.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    resolution_status_display = serializers.CharField(source='get_resolution_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = HospitalCSRAssistant
        fields = '__all__'

class MedicalResearchReviewSerializer(serializers.ModelSerializer):
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    research_type_display = serializers.CharField(source='get_research_type_display', read_only=True)
    quality_rating_display = serializers.CharField(source='get_quality_rating_display', read_only=True)
    evidence_level_display = serializers.CharField(source='get_evidence_level_display', read_only=True)
    reviewed_by_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MedicalResearchReview
        fields = '__all__'

class BackOfficeAutomationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    created_by_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = BackOfficeAutomation
        fields = '__all__'

class ClinicalHistorySearchSerializer(serializers.ModelSerializer):
    searched_by_name = serializers.CharField(source='searched_by.get_full_name', read_only=True)
    patient = PatientSerializer(read_only=True)
    searched_by_id = serializers.IntegerField(write_only=True)
    patient_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    search_type_display = serializers.CharField(source='get_search_type_display', read_only=True)

    class Meta:
        model = ClinicalHistorySearch
        fields = '__all__'


# ============================================================================
# DIABETES MANAGEMENT SERIALIZERS
# ============================================================================

class DiabetesPatientSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    diabetes_type_display = serializers.CharField(source='get_diabetes_type_display', read_only=True)
    insulin_regimen_display = serializers.CharField(source='get_insulin_regimen_display', read_only=True)
    monitoring_method_display = serializers.CharField(source='get_monitoring_method_display', read_only=True)
    smoking_status_display = serializers.CharField(source='get_smoking_status_display', read_only=True)
    
    # Calculated fields
    diabetes_duration_years = serializers.SerializerMethodField()
    latest_hba1c = serializers.SerializerMethodField()
    glucose_readings_count = serializers.SerializerMethodField()
    time_in_range_percentage = serializers.SerializerMethodField()
    average_glucose_30_days = serializers.SerializerMethodField()

    class Meta:
        model = DiabetesPatient
        fields = '__all__'

    def get_diabetes_duration_years(self, obj):
        """Calculate years since diagnosis"""
        today = datetime.now().date()
        duration = today - obj.diagnosis_date
        return round(duration.days / 365.25, 1)

    def get_latest_hba1c(self, obj):
        """Get most recent HbA1c value"""
        latest = obj.hba1c_records.first()
        return latest.hba1c_value if latest else None

    def get_glucose_readings_count(self, obj):
        """Count of glucose readings in last 30 days"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return obj.glucose_readings.filter(reading_datetime__gte=thirty_days_ago).count()

    def get_time_in_range_percentage(self, obj):
        """Calculate time in target range for last 30 days"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_readings = obj.glucose_readings.filter(reading_datetime__gte=thirty_days_ago)
        
        if not recent_readings.exists():
            return None
            
        total_readings = recent_readings.count()
        in_range_readings = recent_readings.filter(
            glucose_value__gte=obj.target_glucose_min,
            glucose_value__lte=obj.target_glucose_max
        ).count()
        
        return round((in_range_readings / total_readings) * 100, 1) if total_readings > 0 else 0

    def get_average_glucose_30_days(self, obj):
        """Calculate average glucose for last 30 days"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        avg_glucose = obj.glucose_readings.filter(
            reading_datetime__gte=thirty_days_ago
        ).aggregate(avg_glucose=Avg('glucose_value'))['avg_glucose']
        
        return round(avg_glucose, 1) if avg_glucose else None


class BloodGlucoseReadingSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    reading_type_display = serializers.CharField(source='get_reading_type_display', read_only=True)
    is_in_target_range = serializers.SerializerMethodField()

    class Meta:
        model = BloodGlucoseReading
        fields = '__all__'

    def get_is_in_target_range(self, obj):
        """Check if reading is in patient's target range"""
        return (obj.diabetes_patient.target_glucose_min <= 
                obj.glucose_value <= 
                obj.diabetes_patient.target_glucose_max)


class HbA1cRecordSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    ordered_by_name = serializers.CharField(source='ordered_by.user.get_full_name', read_only=True)
    estimated_avg_glucose = serializers.SerializerMethodField()

    class Meta:
        model = HbA1cRecord
        fields = '__all__'

    def get_estimated_avg_glucose(self, obj):
        """Calculate estimated average glucose from HbA1c"""
        # Formula: eAG (mg/dL) = 28.7 × A1C - 46.7
        return round((28.7 * obj.hba1c_value) - 46.7, 1)


class DiabetesMedicationSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    prescribed_by_name = serializers.CharField(source='prescribed_by.user.get_full_name', read_only=True)
    medication_type_display = serializers.CharField(source='get_medication_type_display', read_only=True)
    duration_days = serializers.SerializerMethodField()

    class Meta:
        model = DiabetesMedication
        fields = '__all__'

    def get_duration_days(self, obj):
        """Calculate medication duration"""
        end_date = obj.end_date or datetime.now().date()
        duration = end_date - obj.start_date
        return duration.days


class DiabetesComplicationScreeningSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.user.get_full_name', read_only=True)
    screening_type_display = serializers.CharField(source='get_screening_type_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = DiabetesComplicationScreening
        fields = '__all__'

    def get_is_overdue(self, obj):
        """Check if next screening is overdue"""
        if not obj.next_screening_date:
            return False
        return obj.next_screening_date < datetime.now().date()


class DiabetesEducationSessionSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    educator_name = serializers.CharField(source='educator.user.get_full_name', read_only=True)
    education_type_display = serializers.CharField(source='get_education_type_display', read_only=True)

    class Meta:
        model = DiabetesEducationSession
        fields = '__all__'


class DiabetesEmergencyEventSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    duration_hours = serializers.SerializerMethodField()

    class Meta:
        model = DiabetesEmergencyEvent
        fields = '__all__'

    def get_duration_hours(self, obj):
        """Calculate event duration if resolved"""
        if not obj.resolution_datetime:
            return None
        duration = obj.resolution_datetime - obj.event_datetime
        return round(duration.total_seconds() / 3600, 1)


class DiabetesGoalSerializer(serializers.ModelSerializer):
    diabetes_patient_name = serializers.CharField(source='diabetes_patient.patient.user.get_full_name', read_only=True)
    set_by_name = serializers.CharField(source='set_by.user.get_full_name', read_only=True)
    goal_type_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = DiabetesGoal
        fields = '__all__'

    def get_is_overdue(self, obj):
        """Check if goal target date has passed"""
        return obj.target_date < datetime.now().date()

    def get_days_remaining(self, obj):
        """Calculate days until target date"""
        remaining = obj.target_date - datetime.now().date()
        return remaining.days


# Dashboard Analytics Serializers
class DiabetesPatientAnalyticsSerializer(serializers.Serializer):
    """Analytics data for a specific diabetes patient"""
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    diabetes_type = serializers.CharField()
    diagnosis_date = serializers.DateField()
    current_hba1c = serializers.FloatField()
    hba1c_target = serializers.FloatField()
    
    # Recent readings stats
    glucose_readings_30_days = serializers.IntegerField()
    average_glucose_30_days = serializers.FloatField()
    time_in_range_30_days = serializers.FloatField()
    hypoglycemic_episodes_30_days = serializers.IntegerField()
    hyperglycemic_episodes_30_days = serializers.IntegerField()
    
    # Medication adherence
    active_medications_count = serializers.IntegerField()
    
    # Screening status
    overdue_screenings = serializers.ListField(child=serializers.CharField())
    
    # Goals progress
    active_goals_count = serializers.IntegerField()
    achieved_goals_count = serializers.IntegerField()


class DiabetesDashboardStatsSerializer(serializers.Serializer):
    """Overall diabetes program statistics"""
    total_diabetes_patients = serializers.IntegerField()
    patients_by_type = serializers.DictField()
    patients_at_hba1c_target = serializers.IntegerField()


# ========================================
# S3-INTEGRATED SERIALIZERS
# ========================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class MedicalInstitutionSerializer(serializers.ModelSerializer):
    """Serializer for MedicalInstitution model."""
    
    total_patients = serializers.SerializerMethodField()
    total_doctors = serializers.SerializerMethodField()
    storage_used_gb = serializers.SerializerMethodField()
    storage_usage_percentage = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalInstitution
        fields = [
            'id', 'name', 'code', 'address', 'phone', 'email', 'website',
            'license_number', 'accreditation', 'storage_quota_gb',
            'is_active', 'created_at', 'updated_at',
            # Computed fields
            'total_patients', 'total_doctors', 'storage_used_gb',
            'storage_usage_percentage', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_patients(self, obj):
        """Get total number of active patients."""
        return obj.medicine_patients.filter(is_active=True).count()
    
    def get_total_doctors(self, obj):
        """Get total number of active doctors."""
        return obj.doctor_workspaces.filter(is_active=True).count()
    
    def get_storage_used_gb(self, obj):
        """Get total storage used in GB."""
        total_size = obj.medicine_patients.aggregate(
            total=Sum('medical_records__file_size_mb')
        )['total'] or 0
        return round(total_size / 1024, 2)  # Convert MB to GB
    
    def get_storage_usage_percentage(self, obj):
        """Get storage usage percentage."""
        used_gb = self.get_storage_used_gb(obj)
        if obj.storage_quota_gb > 0:
            return round((used_gb / obj.storage_quota_gb) * 100, 1)
        return 0
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class MedicinePatientSerializer(serializers.ModelSerializer):
    """Serializer for MedicinePatient model."""
    
    institution = MedicalInstitutionSerializer(read_only=True)
    institution_id = serializers.UUIDField(write_only=True)
    created_by = UserBasicSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    bmi = serializers.SerializerMethodField()
    blood_pressure = serializers.SerializerMethodField()
    emergency_contact = serializers.SerializerMethodField()
    total_consultations = serializers.SerializerMethodField()
    total_medical_records = serializers.SerializerMethodField()
    last_consultation_date = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    s3_prefix = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicinePatient
        fields = [
            'id', 'institution', 'institution_id', 'patient_code',
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'blood_type', 'phone', 'email', 'address',
            'emergency_contact_name', 'emergency_contact_phone',
            'allergies', 'chronic_conditions', 'current_medications',
            'insurance_provider', 'insurance_number',
            'height_cm', 'weight_kg', 'is_active',
            'created_by', 'created_at', 'updated_at',
            # Computed fields
            'full_name', 'age', 'bmi', 'blood_pressure', 'emergency_contact',
            'total_consultations', 'total_medical_records', 'last_consultation_date',
            'created_at_formatted', 's3_prefix'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get patient's full name."""
        return obj.full_name
    
    def get_age(self, obj):
        """Calculate patient's age."""
        return obj.age
    
    def get_bmi(self, obj):
        """Calculate BMI if height and weight available."""
        return obj.bmi
    
    def get_blood_pressure(self, obj):
        """Get latest blood pressure reading from consultations."""
        latest_consultation = obj.consultations.filter(
            blood_pressure_systolic__isnull=False,
            blood_pressure_diastolic__isnull=False
        ).order_by('-consultation_date').first()
        
        if latest_consultation:
            return latest_consultation.blood_pressure
        return None
    
    def get_emergency_contact(self, obj):
        """Get formatted emergency contact info."""
        if obj.emergency_contact_name and obj.emergency_contact_phone:
            return f"{obj.emergency_contact_name} ({obj.emergency_contact_phone})"
        return obj.emergency_contact_name or obj.emergency_contact_phone or None
    
    def get_total_consultations(self, obj):
        """Get total number of consultations."""
        return obj.consultations.count()
    
    def get_total_medical_records(self, obj):
        """Get total number of medical records."""
        return obj.medical_records.count()
    
    def get_last_consultation_date(self, obj):
        """Get date of last consultation."""
        latest = obj.consultations.order_by('-consultation_date').first()
        return latest.consultation_date.strftime('%Y-%m-%d') if latest else None
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_s3_prefix(self, obj):
        """Get S3 prefix for patient files."""
        return obj.s3_prefix


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""
    
    patient = MedicinePatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    consultation = serializers.SerializerMethodField()
    consultation_id = serializers.UUIDField(write_only=True, required=False)
    created_by = UserBasicSerializer(read_only=True)
    file_size_formatted = serializers.SerializerMethodField()
    record_age_days = serializers.SerializerMethodField()
    s3_url = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'patient_id', 'consultation', 'consultation_id',
            'record_type', 'title', 'description', 's3_key',
            'file_size_mb', 'is_encrypted', 'tags',
            'created_by', 'created_at', 'updated_at',
            # Computed fields
            'file_size_formatted', 'record_age_days', 's3_url',
            'created_at_formatted'
        ]
        read_only_fields = ['id', 's3_key', 'file_size_mb', 'is_encrypted', 'created_at', 'updated_at']
    
    def get_consultation(self, obj):
        """Get basic consultation info if available."""
        if obj.consultation:
            return {
                'id': obj.consultation.id,
                'consultation_date': obj.consultation.consultation_date.strftime('%Y-%m-%d'),
                'consultation_type': obj.consultation.consultation_type,
                'doctor': obj.consultation.doctor.get_full_name() or obj.consultation.doctor.username
            }
        return None
    
    def get_file_size_formatted(self, obj):
        """Get formatted file size."""
        if obj.file_size_mb < 1:
            return f"{round(obj.file_size_mb * 1024, 1)} KB"
        elif obj.file_size_mb < 1024:
            return f"{round(obj.file_size_mb, 1)} MB"
        else:
            return f"{round(obj.file_size_mb / 1024, 1)} GB"
    
    def get_record_age_days(self, obj):
        """Get age of record in days."""
        return (timezone.now().date() - obj.created_at.date()).days
    
    def get_s3_url(self, obj):
        """Get S3 download URL (placeholder - implement with presigned URLs)."""
        # In a real implementation, you would generate a presigned URL here
        return f"s3://{obj.s3_key}" if obj.s3_key else None
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer for Consultation model."""
    
    patient = MedicinePatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    doctor = UserBasicSerializer(read_only=True)
    blood_pressure = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    consultation_date_formatted = serializers.SerializerMethodField()
    vital_signs = serializers.SerializerMethodField()
    has_s3_notes = serializers.SerializerMethodField()
    related_records_count = serializers.SerializerMethodField()
    treatment_plans_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'patient', 'patient_id', 'doctor', 'consultation_type',
            'consultation_date', 'duration_minutes', 'status',
            'chief_complaint', 'history_present_illness', 'examination_findings',
            'assessment', 'plan', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'temperature', 'respiratory_rate', 'oxygen_saturation',
            's3_notes_key', 'created_at', 'updated_at',
            # Computed fields
            'blood_pressure', 'duration_formatted', 'consultation_date_formatted',
            'vital_signs', 'has_s3_notes', 'related_records_count', 'treatment_plans_count'
        ]
        read_only_fields = ['id', 's3_notes_key', 'created_at', 'updated_at']
    
    def get_blood_pressure(self, obj):
        """Get formatted blood pressure."""
        return obj.blood_pressure
    
    def get_duration_formatted(self, obj):
        """Get formatted duration."""
        if obj.duration_minutes:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return None
    
    def get_consultation_date_formatted(self, obj):
        """Get formatted consultation date."""
        return obj.consultation_date.strftime('%Y-%m-%d %H:%M')
    
    def get_vital_signs(self, obj):
        """Get all vital signs in a structured format."""
        return {
            'blood_pressure': obj.blood_pressure,
            'heart_rate': obj.heart_rate,
            'temperature': obj.temperature,
            'respiratory_rate': obj.respiratory_rate,
            'oxygen_saturation': obj.oxygen_saturation
        }
    
    def get_has_s3_notes(self, obj):
        """Check if consultation has S3 notes."""
        return bool(obj.s3_notes_key)
    
    def get_related_records_count(self, obj):
        """Get count of related medical records."""
        return obj.medical_records.count()
    
    def get_treatment_plans_count(self, obj):
        """Get count of related treatment plans."""
        return obj.treatment_plans.count()


class TreatmentPlanSerializer(serializers.ModelSerializer):
    """Serializer for new TreatmentPlan model."""
    
    patient = MedicinePatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    consultation = serializers.SerializerMethodField()
    consultation_id = serializers.UUIDField(write_only=True, required=False)
    created_by = UserBasicSerializer(read_only=True)
    duration_days = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    has_s3_plan = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'id', 'patient', 'patient_id', 'consultation', 'consultation_id',
            'created_by', 'title', 'diagnosis', 'treatment_goals',
            'start_date', 'expected_end_date', 'actual_end_date',
            'status', 'priority', 'progress_notes', 's3_plan_key',
            'created_at', 'updated_at',
            # Computed fields
            'duration_days', 'progress_percentage', 'days_remaining',
            'is_overdue', 'has_s3_plan', 'created_at_formatted'
        ]
        read_only_fields = ['id', 's3_plan_key', 'created_at', 'updated_at']
    
    def get_consultation(self, obj):
        """Get basic consultation info if available."""
        if obj.consultation:
            return {
                'id': obj.consultation.id,
                'consultation_date': obj.consultation.consultation_date.strftime('%Y-%m-%d'),
                'consultation_type': obj.consultation.consultation_type
            }
        return None
    
    def get_duration_days(self, obj):
        """Calculate total duration in days."""
        if obj.expected_end_date:
            return (obj.expected_end_date - obj.start_date).days
        return None
    
    def get_progress_percentage(self, obj):
        """Calculate progress percentage based on dates."""
        if obj.status == 'completed':
            return 100
        elif obj.status == 'cancelled':
            return 0
        elif obj.expected_end_date:
            total_days = (obj.expected_end_date - obj.start_date).days
            elapsed_days = (timezone.now().date() - obj.start_date).days
            if total_days > 0:
                progress = min(100, max(0, (elapsed_days / total_days) * 100))
                return round(progress, 1)
        return 0
    
    def get_days_remaining(self, obj):
        """Calculate days remaining until expected end date."""
        if obj.status in ['completed', 'cancelled']:
            return 0
        elif obj.expected_end_date:
            remaining = (obj.expected_end_date - timezone.now().date()).days
            return max(0, remaining)
        return None
    
    def get_is_overdue(self, obj):
        """Check if treatment plan is overdue."""
        if obj.status in ['completed', 'cancelled']:
            return False
        elif obj.expected_end_date:
            return timezone.now().date() > obj.expected_end_date
        return False
    
    def get_has_s3_plan(self, obj):
        """Check if treatment plan has S3 data."""
        return bool(obj.s3_plan_key)
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class LabResultSerializer(serializers.ModelSerializer):
    """Serializer for LabResult model."""
    
    patient = MedicinePatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    consultation = serializers.SerializerMethodField()
    consultation_id = serializers.UUIDField(write_only=True, required=False)
    ordered_by = UserBasicSerializer(read_only=True)
    turnaround_time_hours = serializers.SerializerMethodField()
    result_age_days = serializers.SerializerMethodField()
    has_s3_results = serializers.SerializerMethodField()
    priority_level = serializers.SerializerMethodField()
    ordered_date_formatted = serializers.SerializerMethodField()
    collection_date_formatted = serializers.SerializerMethodField()
    result_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = LabResult
        fields = [
            'id', 'patient', 'patient_id', 'consultation', 'consultation_id',
            'ordered_by', 'test_name', 'test_category', 'lab_facility',
            'ordered_date', 'collection_date', 'result_date',
            'has_abnormal_values', 'has_critical_values', 'status',
            's3_result_key', 'created_at', 'updated_at',
            # Computed fields
            'turnaround_time_hours', 'result_age_days', 'has_s3_results',
            'priority_level', 'ordered_date_formatted', 'collection_date_formatted',
            'result_date_formatted'
        ]
        read_only_fields = ['id', 's3_result_key', 'created_at', 'updated_at']
    
    def get_consultation(self, obj):
        """Get basic consultation info if available."""
        if obj.consultation:
            return {
                'id': obj.consultation.id,
                'consultation_date': obj.consultation.consultation_date.strftime('%Y-%m-%d'),
                'consultation_type': obj.consultation.consultation_type
            }
        return None
    
    def get_turnaround_time_hours(self, obj):
        """Calculate turnaround time from collection to result."""
        if obj.collection_date and obj.result_date:
            delta = obj.result_date - obj.collection_date
            return round(delta.total_seconds() / 3600, 1)
        return None
    
    def get_result_age_days(self, obj):
        """Get age of result in days."""
        if obj.result_date:
            return (timezone.now().date() - obj.result_date.date()).days
        return None
    
    def get_has_s3_results(self, obj):
        """Check if lab result has S3 data."""
        return bool(obj.s3_result_key)
    
    def get_priority_level(self, obj):
        """Determine priority level based on critical/abnormal values."""
        if obj.has_critical_values:
            return 'critical'
        elif obj.has_abnormal_values:
            return 'abnormal'
        else:
            return 'normal'
    
    def get_ordered_date_formatted(self, obj):
        """Get formatted ordered date."""
        return obj.ordered_date.strftime('%Y-%m-%d %H:%M')
    
    def get_collection_date_formatted(self, obj):
        """Get formatted collection date."""
        return obj.collection_date.strftime('%Y-%m-%d %H:%M') if obj.collection_date else None
    
    def get_result_date_formatted(self, obj):
        """Get formatted result date."""
        return obj.result_date.strftime('%Y-%m-%d %H:%M') if obj.result_date else None


class MedicineAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for MedicineAuditLog model."""
    
    user = UserBasicSerializer(read_only=True)
    institution = serializers.SerializerMethodField()
    timestamp_formatted = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicineAuditLog
        fields = [
            'id', 'action', 'resource_type', 'resource_id',
            'user', 'user_ip', 'institution', 'details',
            'timestamp',
            # Computed fields
            'timestamp_formatted', 'action_display'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_institution(self, obj):
        """Get basic institution info."""
        if obj.institution:
            return {
                'id': obj.institution.id,
                'name': obj.institution.name,
                'code': obj.institution.code
            }
        return None
    
    def get_timestamp_formatted(self, obj):
        """Get formatted timestamp."""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_action_display(self, obj):
        """Get human-readable action description."""
        action_map = {
            'create_institution': 'Created Institution',
            'create_patient': 'Created Patient',
            'upload_record': 'Uploaded Medical Record',
            'create_consultation': 'Created Consultation',
            'create_treatment_plan': 'Created Treatment Plan',
            'upload_lab_result': 'Uploaded Lab Result',
            'access_record': 'Accessed Record',
            'modify_record': 'Modified Record',
            'delete_record': 'Deleted Record'
        }
        return action_map.get(obj.action, obj.action.replace('_', ' ').title())


class DoctorWorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for DoctorWorkspace model."""
    
    doctor = UserBasicSerializer(read_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    institution = MedicalInstitutionSerializer(read_only=True)
    institution_id = serializers.UUIDField(write_only=True)
    total_patients = serializers.SerializerMethodField()
    total_consultations = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorWorkspace
        fields = [
            'id', 'doctor', 'doctor_id', 'institution', 'institution_id',
            'role', 'department', 'specialization', 'license_number',
            'is_active', 'can_create_patients', 'can_modify_records',
            'can_view_all_patients', 'notifications_enabled',
            'created_at', 'updated_at',
            # Computed fields
            'total_patients', 'total_consultations', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_patients(self, obj):
        """Get total number of patients this doctor has consulted."""
        return Consultation.objects.filter(doctor=obj.doctor).values('patient').distinct().count()
    
    def get_total_consultations(self, obj):
        """Get total number of consultations by this doctor."""
        return Consultation.objects.filter(doctor=obj.doctor).count()
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    patients_with_recent_readings = serializers.IntegerField()
    
    # Risk stratification
    high_risk_patients = serializers.IntegerField()
    medium_risk_patients = serializers.IntegerField()
    low_risk_patients = serializers.IntegerField()
    
    # Recent activity
    glucose_readings_this_week = serializers.IntegerField()
    emergency_events_this_month = serializers.IntegerField()
    upcoming_screenings = serializers.IntegerField()
    
    # Quality metrics
    average_time_in_range = serializers.FloatField()
    average_hba1c = serializers.FloatField()
    medication_adherence_rate = serializers.FloatField()
