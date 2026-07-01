from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DermatologyDepartment, SkinCondition, Patient, DermatologyConsultation,
    DiagnosticProcedure, SkinPhoto, TreatmentPlan, TreatmentOutcome, AIAnalysis
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for related fields"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']


class DermatologyDepartmentSerializer(serializers.ModelSerializer):
    """Dermatology Department serializer"""
    head_doctor = UserBasicSerializer(read_only=True)
    head_doctor_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    consultation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DermatologyDepartment
        fields = [
            'id', 'name', 'description', 'head_doctor', 'head_doctor_id',
            'location', 'contact_phone', 'contact_email', 'operating_hours',
            'emergency_services', 'is_active', 'consultation_count',
            'created_at', 'updated_at'
        ]
    
    def get_consultation_count(self, obj):
        return obj.consultations.count()
    
    def validate_head_doctor_id(self, value):
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Doctor not found.")
        return value


class SkinConditionSerializer(serializers.ModelSerializer):
    """Skin Condition serializer"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    treatment_plans_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SkinCondition
        fields = [
            'id', 'name', 'icd10_code', 'category', 'category_display',
            'severity_level', 'severity_display', 'description', 'symptoms',
            'risk_factors', 'treatment_guidelines', 'is_contagious',
            'requires_biopsy', 'typical_duration', 'recurrence_rate',
            'treatment_plans_count', 'is_active', 'created_at', 'updated_at'
        ]
    
    def get_treatment_plans_count(self, obj):
        return obj.treatment_plans.count()


class PatientSerializer(serializers.ModelSerializer):
    """Dermatology Patient serializer"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    skin_type_display = serializers.CharField(source='get_skin_type_display', read_only=True)
    consultations_count = serializers.SerializerMethodField()
    last_consultation = serializers.SerializerMethodField()
    
    # User creation fields for new patients
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False)
    date_of_birth = serializers.DateField(write_only=True, required=False)
    gender = serializers.CharField(write_only=True, required=False)
    address = serializers.CharField(write_only=True, required=False)
    
    # Dermatology specific fields
    emergency_contact = serializers.CharField(write_only=True, required=False, source='emergency_contact_name')
    emergency_phone = serializers.CharField(write_only=True, required=False, source='emergency_contact_phone')
    medical_history = serializers.CharField(write_only=True, required=False, source='family_history')
    allergies = serializers.CharField(write_only=True, required=False, source='known_allergies')
    primary_concern = serializers.CharField(write_only=True, required=False)
    condition = serializers.CharField(write_only=True, required=False)
    severity = serializers.CharField(write_only=True, required=False)
    affected_areas = serializers.CharField(write_only=True, required=False)
    symptoms_duration = serializers.CharField(write_only=True, required=False)
    previous_treatments = serializers.CharField(write_only=True, required=False)
    family_history_skin = serializers.CharField(write_only=True, required=False)
    lifestyle_factors = serializers.CharField(write_only=True, required=False)
    sun_exposure = serializers.CharField(write_only=True, required=False, source='sun_exposure_history')
    skincare_routine = serializers.CharField(write_only=True, required=False)
    insurance_provider = serializers.CharField(write_only=True, required=False)
    insurance_policy = serializers.CharField(write_only=True, required=False, source='insurance_policy_number')
    preferred_communication = serializers.CharField(write_only=True, required=False)
    consent_treatment = serializers.BooleanField(write_only=True, required=False)
    consent_photos = serializers.BooleanField(write_only=True, required=False)
    consent_marketing = serializers.BooleanField(write_only=True, required=False)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'user_id', 'medical_record_number', 'skin_type',
            'skin_type_display', 'family_history', 'known_allergies',
            'current_medications', 'sun_exposure_history', 'occupation',
            'smoking_status', 'alcohol_consumption', 'previous_skin_cancer',
            'emergency_contact_name', 'emergency_contact_phone',
            'insurance_provider', 'insurance_policy_number',
            'consultations_count', 'last_consultation', 'created_at', 'updated_at',
            # User creation fields
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'address',
            # Additional dermatology fields
            'emergency_contact', 'emergency_phone', 'medical_history', 'allergies',
            'primary_concern', 'condition', 'severity', 'affected_areas', 'symptoms_duration',
            'previous_treatments', 'family_history_skin', 'lifestyle_factors', 'sun_exposure',
            'skincare_routine', 'insurance_policy', 'preferred_communication',
            'consent_treatment', 'consent_photos', 'consent_marketing'
        ]
    
    def get_consultations_count(self, obj):
        return obj.dermatology_consultations.count()
    
    def get_last_consultation(self, obj):
        last_consultation = obj.dermatology_consultations.order_by('-scheduled_date').first()
        if last_consultation:
            return {
                'id': last_consultation.id,
                'consultation_number': last_consultation.consultation_number,
                'scheduled_date': last_consultation.scheduled_date,
                'status': last_consultation.status
            }
        return None
    
    def validate_user_id(self, value):
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value
    
    def create(self, validated_data):
        # Extract user-related data
        user_data = {}
        user_fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'address']
        
        for field in user_fields:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        # Remove frontend-only fields that don't map to model fields
        frontend_only_fields = [
            'primary_concern', 'condition', 'severity', 'affected_areas', 
            'symptoms_duration', 'previous_treatments', 'family_history_skin',
            'lifestyle_factors', 'skincare_routine', 'preferred_communication',
            'consent_treatment', 'consent_photos', 'consent_marketing'
        ]
        
        for field in frontend_only_fields:
            validated_data.pop(field, None)
        
        # Create or get user
        if 'user_id' in validated_data and validated_data['user_id']:
            # Use existing user
            user = User.objects.get(id=validated_data.pop('user_id'))
        elif user_data.get('email'):
            # Create new user
            import uuid
            user = User.objects.create_user(
                username=user_data.get('email'),
                email=user_data.get('email'),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                phone_number=user_data.get('phone', ''),
                role='patient'
            )
        else:
            raise serializers.ValidationError("Either user_id or email is required.")
        
        # Generate medical record number if not provided
        if 'medical_record_number' not in validated_data:
            import uuid
            validated_data['medical_record_number'] = f"DERM-{uuid.uuid4().hex[:8].upper()}"
        
        # Create patient
        patient = Patient.objects.create(user=user, **validated_data)
        return patient
        if Patient.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Patient profile already exists for this user.")
        return value


class DiagnosticProcedureSerializer(serializers.ModelSerializer):
    """Diagnostic Procedure serializer"""
    procedure_type_display = serializers.CharField(source='get_procedure_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    performed_by = UserBasicSerializer(read_only=True)
    performed_by_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = DiagnosticProcedure
        fields = [
            'id', 'procedure_number', 'consultation', 'procedure_type',
            'procedure_type_display', 'procedure_name', 'indication',
            'anatomical_location', 'procedure_date', 'performed_by',
            'performed_by_id', 'status', 'status_display', 'procedure_details',
            'findings', 'complications', 'post_procedure_care',
            'created_at', 'updated_at'
        ]


class SkinPhotoSerializer(serializers.ModelSerializer):
    """Skin Photo serializer"""
    photo_type_display = serializers.CharField(source='get_photo_type_display', read_only=True)
    anatomical_region_display = serializers.CharField(source='get_anatomical_region_display', read_only=True)
    taken_by = UserBasicSerializer(read_only=True)
    taken_by_id = serializers.UUIDField(write_only=True)
    ai_analyses_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SkinPhoto
        fields = [
            'id', 'consultation', 'photo_type', 'photo_type_display',
            'anatomical_region', 'anatomical_region_display', 'specific_location',
            'image_file', 'thumbnail', 'image_url', 'thumbnail_url', 'description',
            'magnification', 'lighting_conditions', 'camera_settings',
            'taken_by', 'taken_by_id', 'taken_at', 'is_before_treatment',
            'is_after_treatment', 'treatment_day', 'consent_obtained',
            'research_use_permitted', 'teaching_use_permitted',
            'ai_analyses_count', 'created_at', 'updated_at'
        ]
    
    def get_ai_analyses_count(self, obj):
        return obj.ai_analyses.count()
    
    def get_image_url(self, obj):
        if obj.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_file.url)
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None


class TreatmentPlanSerializer(serializers.ModelSerializer):
    """Treatment Plan serializer"""
    treatment_category_display = serializers.CharField(source='get_treatment_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    diagnosed_condition = SkinConditionSerializer(read_only=True)
    diagnosed_condition_id = serializers.UUIDField(write_only=True)
    prescribed_by = UserBasicSerializer(read_only=True)
    prescribed_by_id = serializers.UUIDField(write_only=True)
    outcomes_count = serializers.SerializerMethodField()
    latest_outcome = serializers.SerializerMethodField()
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'id', 'consultation', 'diagnosed_condition', 'diagnosed_condition_id',
            'treatment_category', 'treatment_category_display', 'treatment_name',
            'treatment_description', 'medication_name', 'dosage', 'frequency',
            'duration', 'application_instructions', 'precautions',
            'expected_outcomes', 'potential_side_effects', 'start_date',
            'expected_end_date', 'actual_end_date', 'status', 'status_display',
            'effectiveness_rating', 'patient_compliance', 'treatment_notes',
            'prescribed_by', 'prescribed_by_id', 'outcomes_count',
            'latest_outcome', 'created_at', 'updated_at'
        ]
    
    def get_outcomes_count(self, obj):
        return obj.outcomes.count()
    
    def get_latest_outcome(self, obj):
        latest_outcome = obj.outcomes.order_by('-assessment_date').first()
        if latest_outcome:
            return {
                'id': latest_outcome.id,
                'assessment_date': latest_outcome.assessment_date,
                'outcome_status': latest_outcome.outcome_status,
                'improvement_percentage': latest_outcome.improvement_percentage
            }
        return None


class TreatmentOutcomeSerializer(serializers.ModelSerializer):
    """Treatment Outcome serializer"""
    outcome_status_display = serializers.CharField(source='get_outcome_status_display', read_only=True)
    treatment_plan = TreatmentPlanSerializer(read_only=True)
    treatment_plan_id = serializers.UUIDField(write_only=True)
    assessed_by = UserBasicSerializer(read_only=True)
    assessed_by_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = TreatmentOutcome
        fields = [
            'id', 'treatment_plan', 'treatment_plan_id', 'assessment_date',
            'outcome_status', 'outcome_status_display', 'improvement_percentage',
            'symptom_severity_score', 'patient_satisfaction', 'side_effects_reported',
            'quality_of_life_impact', 'objective_measurements', 'clinical_notes',
            'next_assessment_date', 'treatment_modifications', 'assessed_by',
            'assessed_by_id', 'created_at', 'updated_at'
        ]


class AIAnalysisSerializer(serializers.ModelSerializer):
    """AI Analysis serializer"""
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    confidence_level_display = serializers.CharField(source='get_confidence_level_display', read_only=True)
    skin_photo = SkinPhotoSerializer(read_only=True)
    skin_photo_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = AIAnalysis
        fields = [
            'id', 'skin_photo', 'skin_photo_id', 'analysis_type',
            'analysis_type_display', 'ai_model_version', 'analysis_date',
            'confidence_level', 'confidence_level_display', 'confidence_score',
            'primary_findings', 'secondary_findings', 'risk_assessment',
            'recommended_actions', 'differential_diagnosis', 'feature_analysis',
            'lesion_measurements', 'color_analysis', 'texture_metrics',
            'asymmetry_score', 'border_irregularity', 'color_variation',
            'diameter_mm', 'evolution_detected', 'requires_biopsy',
            'urgency_level', 'validated_by_doctor', 'doctor_agreement',
            'doctor_notes', 'processing_time_seconds', 'created_at', 'updated_at'
        ]


class DermatologyConsultationSerializer(serializers.ModelSerializer):
    """Dermatology Consultation serializer"""
    consultation_type_display = serializers.CharField(source='get_consultation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    dermatologist = UserBasicSerializer(read_only=True)
    dermatologist_id = serializers.UUIDField(write_only=True)
    department = DermatologyDepartmentSerializer(read_only=True)
    department_id = serializers.UUIDField(write_only=True)
    created_by = UserBasicSerializer(read_only=True)
    created_by_id = serializers.UUIDField(write_only=True)
    
    # Related data counts
    diagnostic_procedures_count = serializers.SerializerMethodField()
    skin_photos_count = serializers.SerializerMethodField()
    treatment_plans_count = serializers.SerializerMethodField()
    
    # Nested data (optional)
    diagnostic_procedures = DiagnosticProcedureSerializer(many=True, read_only=True)
    skin_photos = SkinPhotoSerializer(many=True, read_only=True)
    treatment_plans = TreatmentPlanSerializer(many=True, read_only=True)
    
    class Meta:
        model = DermatologyConsultation
        fields = [
            'id', 'consultation_number', 'patient', 'patient_id',
            'dermatologist', 'dermatologist_id', 'department', 'department_id',
            'consultation_type', 'consultation_type_display', 'scheduled_date',
            'actual_start_time', 'actual_end_time', 'status', 'status_display',
            'priority', 'priority_display', 'chief_complaint',
            'history_of_present_illness', 'review_of_systems',
            'physical_examination', 'assessment', 'plan',
            'follow_up_instructions', 'next_appointment_recommended',
            'consultation_notes', 'created_by', 'created_by_id',
            'diagnostic_procedures_count', 'skin_photos_count',
            'treatment_plans_count', 'diagnostic_procedures',
            'skin_photos', 'treatment_plans', 'created_at', 'updated_at'
        ]
    
    def get_diagnostic_procedures_count(self, obj):
        return obj.diagnostic_procedures.count()
    
    def get_skin_photos_count(self, obj):
        return obj.skin_photos.count()
    
    def get_treatment_plans_count(self, obj):
        return obj.treatment_plans.count()
    
    def to_representation(self, instance):
        # Conditionally include nested data based on context
        representation = super().to_representation(instance)
        
        # Remove nested data for list views to improve performance
        if self.context.get('request') and self.context['request'].resolver_match.url_name.endswith('list'):
            representation.pop('diagnostic_procedures', None)
            representation.pop('skin_photos', None)
            representation.pop('treatment_plans', None)
        
        return representation


# Summary/Dashboard Serializers
class DermatologyDashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics for dermatology department"""
    total_patients = serializers.IntegerField()
    total_consultations = serializers.IntegerField()
    consultations_today = serializers.IntegerField()
    consultations_this_week = serializers.IntegerField()
    consultations_this_month = serializers.IntegerField()
    pending_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    total_diagnostic_procedures = serializers.IntegerField()
    total_skin_photos = serializers.IntegerField()
    total_ai_analyses = serializers.IntegerField()
    total_treatment_plans = serializers.IntegerField()
    active_treatment_plans = serializers.IntegerField()
    departments_count = serializers.IntegerField()
    skin_conditions_count = serializers.IntegerField()


class ConsultationSummarySerializer(serializers.ModelSerializer):
    """Simplified consultation serializer for lists and summaries"""
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    dermatologist_name = serializers.CharField(source='dermatologist.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = DermatologyConsultation
        fields = [
            'id', 'consultation_number', 'patient_name', 'dermatologist_name',
            'department_name', 'consultation_type', 'scheduled_date',
            'status', 'priority', 'chief_complaint', 'created_at'
        ]
