from rest_framework import serializers
from .models import Patient, MedicalHistory, Appointment, VitalSigns, LabResult
from .advanced_models import (
    PatientAdmission, PatientJourney, AIPatientInsights, 
    PatientReport, PatientMetrics
)
from django.contrib.auth import get_user_model

User = get_user_model()

class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    primary_physician_name = serializers.CharField(source='primary_physician.get_full_name', read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Auto-generate patient ID
        last_patient = Patient.objects.order_by('-id').first()
        if last_patient and last_patient.patient_id and '-' in last_patient.patient_id:
            try:
                last_id = int(last_patient.patient_id.split('-')[-1])
                new_id = f"PAT-{last_id + 1:06d}"
            except (ValueError, IndexError):
                new_id = "PAT-000001"
        else:
            new_id = "PAT-000001"
        
        validated_data['patient_id'] = new_id
        return super().create(validated_data)

class PatientSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for patient lists"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = ['id', 'patient_id', 'full_name', 'age', 'gender', 'phone_number', 'email']

class MedicalHistorySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    diagnosed_by_name = serializers.CharField(source='diagnosed_by.get_full_name', read_only=True)
    
    class Meta:
        model = MedicalHistory
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    appointment_datetime = serializers.ReadOnlyField()
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['appointment_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Auto-generate appointment ID
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        validated_data['appointment_id'] = f"APT-{timestamp}"
        return super().create(validated_data)

class VitalSignsSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    measured_by_name = serializers.CharField(source='measured_by.get_full_name', read_only=True)
    bmi = serializers.ReadOnlyField()
    
    class Meta:
        model = VitalSigns
        fields = '__all__'

class LabResultSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    ordered_by_name = serializers.CharField(source='ordered_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = LabResult
        fields = '__all__'

# Dashboard serializers for statistics
class PatientStatsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    new_patients_this_month = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    pending_lab_results = serializers.IntegerField()
    
class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for doctor/user selection"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name']

# Advanced Patient Management Serializers

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class PatientBasicSerializer(serializers.ModelSerializer):
    """Basic patient information for nested serialization"""
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'age', 'gender', 'phone_number', 'email']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None

class PatientAdmissionSerializer(serializers.ModelSerializer):
    """Comprehensive Patient Admission Serializer"""
    patient_details = PatientBasicSerializer(source='patient', read_only=True)
    attending_physician_details = UserBasicSerializer(source='attending_physician', read_only=True)
    created_by_details = UserBasicSerializer(source='created_by', read_only=True)
    length_of_stay = serializers.ReadOnlyField()
    is_discharged = serializers.ReadOnlyField()
    
    # Statistics fields
    journey_events_count = serializers.SerializerMethodField()
    ai_insights_count = serializers.SerializerMethodField()
    reports_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientAdmission
        fields = [
            'id', 'admission_id', 'patient', 'patient_details',
            'attending_physician', 'attending_physician_details',
            'admission_date', 'admission_type', 'department',
            'room_number', 'bed_number', 'chief_complaint',
            'initial_diagnosis', 'medical_history', 'allergies',
            'current_medications', 'current_status', 'priority_level',
            'insurance_provider', 'insurance_policy_number', 'estimated_cost',
            'discharge_date', 'discharge_diagnosis', 'discharge_instructions',
            'discharge_medications', 'follow_up_required', 'follow_up_date',
            'ai_risk_score', 'ai_predictions', 'created_by', 'created_by_details',
            'created_at', 'updated_at', 'is_active', 'length_of_stay',
            'is_discharged', 'journey_events_count', 'ai_insights_count',
            'reports_count'
        ]
        read_only_fields = ['admission_id', 'created_by', 'created_at', 'updated_at']
    
    def get_journey_events_count(self, obj):
        return obj.journey_events.count()
    
    def get_ai_insights_count(self, obj):
        return obj.ai_insights.count()
    
    def get_reports_count(self, obj):
        return obj.reports.count()

class PatientJourneySerializer(serializers.ModelSerializer):
    """Patient Journey Event Serializer"""
    admission_details = serializers.SerializerMethodField()
    patient_details = PatientBasicSerializer(source='patient', read_only=True)
    staff_member_details = UserBasicSerializer(source='staff_member', read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    
    class Meta:
        model = PatientJourney
        fields = [
            'id', 'admission', 'admission_details', 'patient', 'patient_details',
            'stage', 'stage_display', 'timestamp', 'location', 'action_taken',
            'staff_member', 'staff_member_details', 'vital_signs', 'notes',
            'duration_minutes', 'wait_time_minutes'
        ]
    
    def get_admission_details(self, obj):
        return {
            'admission_id': obj.admission.admission_id,
            'status': obj.admission.current_status,
            'department': obj.admission.department
        }

class AIPatientInsightsSerializer(serializers.ModelSerializer):
    """AI Patient Insights Serializer"""
    admission_details = serializers.SerializerMethodField()
    patient_details = PatientBasicSerializer(source='patient', read_only=True)
    validated_by_details = UserBasicSerializer(source='validated_by', read_only=True)
    insight_type_display = serializers.CharField(source='get_insight_type_display', read_only=True)
    risk_level = serializers.SerializerMethodField()
    
    class Meta:
        model = AIPatientInsights
        fields = [
            'id', 'admission', 'admission_details', 'patient', 'patient_details',
            'insight_type', 'insight_type_display', 'confidence_level',
            'prediction_data', 'recommendations', 'risk_factors', 'risk_score',
            'risk_level', 'accuracy_score', 'generated_at', 'validated_by',
            'validated_by_details', 'is_validated', 'validation_notes'
        ]
    
    def get_admission_details(self, obj):
        return {
            'admission_id': obj.admission.admission_id,
            'patient_name': obj.patient.first_name + ' ' + obj.patient.last_name,
            'current_status': obj.admission.current_status
        }
    
    def get_risk_level(self, obj):
        if obj.risk_score >= 7:
            return 'High'
        elif obj.risk_score >= 4:
            return 'Medium'
        else:
            return 'Low'

class PatientReportSerializer(serializers.ModelSerializer):
    """Patient Report Serializer"""
    admission_details = serializers.SerializerMethodField()
    patient_details = PatientBasicSerializer(source='patient', read_only=True)
    generated_by_details = UserBasicSerializer(source='generated_by', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientReport
        fields = [
            'id', 'admission', 'admission_details', 'patient', 'patient_details',
            'report_id', 'report_type', 'report_type_display', 'title',
            'summary', 'file_format', 'generated_by', 'generated_by_details',
            'generated_at', 'status', 'download_url'
        ]
    
    def get_admission_details(self, obj):
        return {
            'admission_id': obj.admission.admission_id,
            'patient_name': obj.patient.first_name + ' ' + obj.patient.last_name,
            'admission_date': obj.admission.admission_date
        }
    
    def get_download_url(self, obj):
        if obj.status == 'completed':
            return f"/api/reports/{obj.report_id}/download/"
        return None

class PatientMetricsSerializer(serializers.ModelSerializer):
    """Patient Care Metrics Serializer"""
    admission_details = serializers.SerializerMethodField()
    patient_details = PatientBasicSerializer(source='patient', read_only=True)
    care_quality_score = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientMetrics
        fields = [
            'id', 'admission', 'admission_details', 'patient', 'patient_details',
            'door_to_doctor_minutes', 'satisfaction_score', 'total_cost',
            'readmission_30_days', 'treatment_successful', 'care_quality_score'
        ]
    
    def get_admission_details(self, obj):
        return {
            'admission_id': obj.admission.admission_id,
            'length_of_stay': obj.admission.length_of_stay,
            'status': obj.admission.current_status
        }
    
    def get_care_quality_score(self, obj):
        """Calculate overall care quality score (0-100)"""
        score = 100
        if obj.readmission_30_days:
            score -= 15
        if not obj.treatment_successful:
            score -= 20
        if obj.satisfaction_score and obj.satisfaction_score >= 8:
            score += 5
        return max(score, 0)
