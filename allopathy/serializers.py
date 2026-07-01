from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    AllopathyHospital,
    AllopathyPatientS3,
    AllopathyFile,
    AllopathyAnalysis,
    AllopathyMedicalRecord,
    AllopathyTreatmentPlan
)

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class AllopathyHospitalSerializer(serializers.ModelSerializer):
    """Serializer for AllopathyHospital model"""
    patient_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyHospital
        fields = [
            'id', 'name', 'hospital_type', 'license_number', 'chief_physician',
            'address', 'city', 'state', 'postal_code', 'phone', 'email',
            'website', 'bed_capacity', 'specialties', 'accreditation', 'status',
            's3_bucket', 's3_region', 'patient_count', 'file_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient_count', 'file_count']
    
    def get_patient_count(self, obj):
        return obj.patients.count()
    
    def get_file_count(self, obj):
        return obj.files.count()

class AllopathyPatientS3Serializer(serializers.ModelSerializer):
    """Serializer for AllopathyPatientS3 model"""
    hospital_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    analysis_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyPatientS3
        fields = [
            'id', 'hospital', 'hospital_name', 'patient_id', 'first_name', 'last_name',
            'full_name', 'date_of_birth', 'age', 'gender', 'blood_group', 'phone',
            'email', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            'admission_date', 'admission_type', 'attending_physician', 'insurance_provider',
            'insurance_number', 'allergies', 'current_medications', 'medical_history',
            'vital_signs', 'status', 'notes', 'file_count', 'analysis_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'hospital_name', 'full_name',
            'file_count', 'analysis_count'
        ]
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_file_count(self, obj):
        return obj.files.count()
    
    def get_analysis_count(self, obj):
        return obj.analyses.count()
    
    def validate_patient_id(self, value):
        """Validate patient ID uniqueness"""
        if AllopathyPatientS3.objects.filter(patient_id=value).exists():
            if self.instance and self.instance.patient_id != value:
                raise serializers.ValidationError("Patient ID already exists")
        return value

class AllopathyFileSerializer(serializers.ModelSerializer):
    """Serializer for AllopathyFile model"""
    hospital_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyFile
        fields = [
            'id', 'hospital', 'hospital_name', 'patient', 'patient_name',
            'filename', 'original_name', 'category', 'file_size', 'file_size_mb',
            'file_type', 'file_hash', 's3_key', 's3_bucket', 'upload_date',
            'uploaded_by', 'uploaded_by_name', 'download_url', 'expiry_date',
            'is_confidential', 'access_level', 'status', 'metadata', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_hash', 's3_key', 'upload_date', 'uploaded_by',
            'created_at', 'updated_at', 'hospital_name', 'patient_name',
            'uploaded_by_name', 'file_size_mb'
        ]
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip()
        return None
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)

class AllopathyAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for AllopathyAnalysis model"""
    hospital_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyAnalysis
        fields = [
            'id', 'hospital', 'hospital_name', 'patient', 'patient_name',
            'file', 'file_name', 'analysis_type', 'input_data', 'results',
            'confidence_score', 'confidence_percentage', 'recommendations',
            'risk_factors', 'follow_up_required', 'follow_up_date',
            'reviewed_by', 'reviewed_by_name', 'review_notes', 'status',
            'processing_time', 'ai_model_version', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'hospital_name', 'patient_name',
            'file_name', 'reviewed_by_name', 'confidence_percentage'
        ]
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None
    
    def get_file_name(self, obj):
        return obj.file.original_name if obj.file else None
    
    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}".strip()
        return None
    
    def get_confidence_percentage(self, obj):
        return round(obj.confidence_score * 100, 2)
    
    def validate_confidence_score(self, value):
        """Validate confidence score is between 0 and 1"""
        if not 0 <= value <= 1:
            raise serializers.ValidationError("Confidence score must be between 0 and 1")
        return value

class AllopathyMedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for AllopathyMedicalRecord model"""
    patient_name = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyMedicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'admission_date', 'discharge_date',
            'duration_days', 'chief_complaint', 'history_of_present_illness',
            'past_medical_history', 'family_history', 'social_history',
            'review_of_systems', 'physical_examination', 'assessment_and_plan',
            'attending_physician', 'department', 'room_number', 'diagnosis_codes',
            'procedures', 'lab_orders', 'imaging_orders', 'consultations',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient_name', 'duration_days']
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None
    
    def get_duration_days(self, obj):
        if obj.discharge_date and obj.admission_date:
            return (obj.discharge_date.date() - obj.admission_date.date()).days
        return None

class AllopathyTreatmentPlanSerializer(serializers.ModelSerializer):
    """Serializer for AllopathyTreatmentPlan model"""
    patient_name = serializers.SerializerMethodField()
    medical_record_date = serializers.SerializerMethodField()
    medications_count = serializers.SerializerMethodField()
    procedures_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AllopathyTreatmentPlan
        fields = [
            'id', 'patient', 'patient_name', 'medical_record', 'medical_record_date',
            'plan_date', 'diagnosis', 'treatment_plan', 'medications', 'medications_count',
            'procedures_planned', 'procedures_count', 'follow_up_instructions',
            'diet_instructions', 'activity_restrictions', 'prescribed_by', 'priority',
            'expected_duration', 'review_date', 'goals', 'contraindications',
            'monitoring_parameters', 'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'patient_name', 'medical_record_date',
            'medications_count', 'procedures_count'
        ]
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None
    
    def get_medical_record_date(self, obj):
        if obj.medical_record:
            return obj.medical_record.admission_date
        return None
    
    def get_medications_count(self, obj):
        return len(obj.medications) if obj.medications else 0
    
    def get_procedures_count(self, obj):
        return len(obj.procedures_planned) if obj.procedures_planned else 0

# Detailed serializers for comprehensive data views
class AllopathyPatientDetailSerializer(AllopathyPatientS3Serializer):
    """Detailed serializer for patient with related data"""
    files = AllopathyFileSerializer(many=True, read_only=True)
    analyses = AllopathyAnalysisSerializer(many=True, read_only=True)
    medical_records = AllopathyMedicalRecordSerializer(many=True, read_only=True)
    treatment_plans = AllopathyTreatmentPlanSerializer(many=True, read_only=True)
    
    class Meta(AllopathyPatientS3Serializer.Meta):
        fields = AllopathyPatientS3Serializer.Meta.fields + [
            'files', 'analyses', 'medical_records', 'treatment_plans'
        ]

class AllopathyAnalysisDetailSerializer(AllopathyAnalysisSerializer):
    """Detailed serializer for analysis with related data"""
    hospital = AllopathyHospitalSerializer(read_only=True)
    patient = AllopathyPatientS3Serializer(read_only=True)
    file = AllopathyFileSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta(AllopathyAnalysisSerializer.Meta):
        fields = AllopathyAnalysisSerializer.Meta.fields + [
            'hospital', 'patient', 'file', 'reviewed_by'
        ]
