from rest_framework import serializers
from .models import HomeopathyPatient, HomeopathyRemedy, HomeopathyDiagnosis, HomeopathyRemedySuggestion
from django.contrib.auth import get_user_model

User = get_user_model()

class HomeopathyPatientSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = HomeopathyPatient
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class HomeopathyRemedySerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeopathyRemedy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class HomeopathyRemedyListSerializer(serializers.ModelSerializer):
    """Simplified remedy serializer for lists"""
    class Meta:
        model = HomeopathyRemedy
        fields = ['id', 'name', 'latin_name', 'common_name', 'miasm']

class HomeopathyRemedySuggestionSerializer(serializers.ModelSerializer):
    remedy = HomeopathyRemedyListSerializer(read_only=True)
    
    class Meta:
        model = HomeopathyRemedySuggestion
        fields = '__all__'
        read_only_fields = ['created_at']

class HomeopathyDiagnosisSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    practitioner_name = serializers.CharField(source='practitioner.username', read_only=True)
    remedy_suggestions = HomeopathyRemedySuggestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = HomeopathyDiagnosis
        fields = '__all__'
        read_only_fields = ['practitioner', 'created_at', 'updated_at', 'analyzed_at']
    
    def create(self, validated_data):
        validated_data['practitioner'] = self.context['request'].user
        return super().create(validated_data)

class DiagnosisCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating diagnosis with all data"""
    class Meta:
        model = HomeopathyDiagnosis
        exclude = ['practitioner', 'created_at', 'updated_at', 'analyzed_at']
        read_only_fields = ['ai_confidence', 'suggested_constitution', 'suggested_miasm',
                           'mental_emotional_score', 'physical_score', 'modality_score',
                           'status']
    
    def create(self, validated_data):
        validated_data['practitioner'] = self.context['request'].user
        return super().create(validated_data)

class AIAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for AI analysis request data"""
    # Patient info
    patient_id = serializers.IntegerField()
    
    # Chief complaints
    primary_symptoms = serializers.CharField()
    duration = serializers.CharField(required=False, allow_blank=True)
    onset = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.IntegerField(min_value=1, max_value=10, default=5)
    
    # Mental & Emotional
    mental_state = serializers.CharField(required=False, allow_blank=True)
    emotional_pattern = serializers.CharField(required=False, allow_blank=True)
    fears = serializers.CharField(required=False, allow_blank=True)
    anxieties = serializers.CharField(required=False, allow_blank=True)
    mood = serializers.CharField(required=False, allow_blank=True)
    
    # Physical generals
    appetite = serializers.CharField(required=False, allow_blank=True)
    thirst = serializers.CharField(required=False, allow_blank=True)
    sleep = serializers.CharField(required=False, allow_blank=True)
    dreams = serializers.CharField(required=False, allow_blank=True)
    thermals = serializers.CharField(required=False, allow_blank=True)
    perspiration = serializers.CharField(required=False, allow_blank=True)
    
    # Modalities
    better_by = serializers.CharField(required=False, allow_blank=True)
    worse_by = serializers.CharField(required=False, allow_blank=True)
    time_aggravation = serializers.CharField(required=False, allow_blank=True)
    
    # Constitutional
    energy = serializers.CharField(required=False, allow_blank=True)
    circulation = serializers.CharField(required=False, allow_blank=True)
    digestion = serializers.CharField(required=False, allow_blank=True)
    elimination = serializers.CharField(required=False, allow_blank=True)
    
    # Miasmatic
    family_history = serializers.CharField(required=False, allow_blank=True)
    past_illness = serializers.CharField(required=False, allow_blank=True)
    
    # Additional
    lifestyle = serializers.CharField(required=False, allow_blank=True)
    environment = serializers.CharField(required=False, allow_blank=True)
    stress_factors = serializers.CharField(required=False, allow_blank=True)
    previous_treatments = serializers.CharField(required=False, allow_blank=True)

class AIAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for AI analysis response"""
    diagnosis_id = serializers.IntegerField()
    ai_confidence = serializers.FloatField()
    suggested_constitution = serializers.CharField()
    suggested_miasm = serializers.CharField()
    mental_emotional_score = serializers.IntegerField()
    physical_score = serializers.IntegerField()
    modality_score = serializers.IntegerField()
    estimated_duration = serializers.CharField()
    suggested_potency = serializers.CharField()
    suggested_frequency = serializers.CharField()
    follow_up_recommendations = serializers.ListField()
    remedy_suggestions = HomeopathyRemedySuggestionSerializer(many=True)
