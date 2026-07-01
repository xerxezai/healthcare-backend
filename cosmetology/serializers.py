from rest_framework import serializers
from .models import (
    CosmetologyClient, CosmetologyService, CosmetologyProduct,
    CosmetologyAppointment, CosmetologyTreatmentPlan, CosmetologyConsultation,
    CosmetologyProgress, TreatmentPlanService, TreatmentPlanProduct,
    # S3 Models
    CosmetologySalon, CosmetologyClientS3,
    CosmetologyFile, CosmetologyAnalysis,
    # Cosmetic Gynecology Models
    CosmeticGynecologyClient, CosmeticGynecologyTreatment, CosmeticGynecologyConsultation,
    CosmeticGynecologyTreatmentPlan, CosmeticGynecologyProgress
)
from django.contrib.auth import get_user_model

User = get_user_model()

# S3 Data Management Serializers

class CosmetologySalonSerializer(serializers.ModelSerializer):
    """Serializer for cosmetology salon/institution with S3 integration"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    institution_type_display = serializers.CharField(source='get_institution_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CosmetologySalon
        fields = [
            'salon_id', 'name', 'institution_type', 'institution_type_display',
            'license_number', 'accreditation_body', 'head_aesthetician',
            'phone', 'email', 'website', 'address', 'city', 'state', 'zip_code',
            'operating_hours', 'emergency_contact', 's3_bucket', 's3_folder_path',
            's3_folders', 'status', 'status_display', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'client_count', 'file_count'
        ]
        read_only_fields = ['salon_id', 'created_by', 'created_at', 'updated_at']
    
    def get_client_count(self, obj):
        return obj.clients.filter(status='active').count()
    
    def get_file_count(self, obj):
        return CosmetologyFile.objects.filter(salon=obj, status='uploaded').count()

class CosmetologyClientS3Serializer(serializers.ModelSerializer):
    """Serializer for cosmetology client with S3 integration"""
    salon_name = serializers.CharField(source='salon.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    skin_type_display = serializers.CharField(source='get_skin_type_display', read_only=True)
    fitzpatrick_display = serializers.CharField(source='get_fitzpatrick_scale_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    treatment_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CosmetologyClientS3
        fields = [
            'client_id', 'salon', 'salon_name', 'client_external_id',
            'first_name', 'last_name', 'full_name', 'date_of_birth', 'age',
            'gender', 'phone', 'email', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'referring_source', 'skin_type',
            'skin_type_display', 'fitzpatrick_scale', 'fitzpatrick_display',
            'allergies', 'skin_concerns', 'beauty_goals', 's3_folder_path',
            's3_folders', 'status', 'status_display', 'created_at', 'updated_at',
            'last_visit', 'treatment_count', 'file_count'
        ]
        read_only_fields = ['client_id', 'created_at', 'updated_at', 'last_visit']
    
    def get_treatment_count(self, obj):
        # This would need to be implemented when treatment model is available
        return 0
    
    def get_file_count(self, obj):
        return CosmetologyFile.objects.filter(client=obj, status='uploaded').count()

class CosmetologyFileSerializer(serializers.ModelSerializer):
    """Serializer for cosmetology files with S3 storage"""
    salon_name = serializers.CharField(source='salon.name', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = CosmetologyFile
        fields = [
            'file_id', 'salon', 'salon_name', 'client', 'client_name',
            'original_name', 'filename', 'file_size',
            'file_size_formatted', 'content_type', 'category', 'category_display',
            's3_key', 's3_bucket', 's3_url', 'description', 'tags', 'metadata',
            'status', 'status_display', 'upload_date', 'last_accessed',
            'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = [
            'file_id', 'filename', 'file_size', 's3_key', 's3_bucket', 's3_url',
            'upload_date', 'last_accessed', 'uploaded_by'
        ]

class CosmetologyAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for AI analysis results"""
    salon_name = serializers.CharField(source='salon.name', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    file_name = serializers.CharField(source='file.original_name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    validated_by_name = serializers.CharField(source='validated_by.username', read_only=True)
    confidence_percentage = serializers.SerializerMethodField()
    processing_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CosmetologyAnalysis
        fields = [
            'analysis_id', 'salon', 'salon_name', 'client', 'client_name',
            'file', 'file_name', 'analysis_type', 'analysis_type_display',
            'analysis_date', 'ai_model_used', 'confidence_score', 'confidence_percentage',
            'analysis_results', 'recommendations', 'risk_factors', 'follow_up_needed',
            'validated_by', 'validated_by_name', 'validation_date', 'validation_notes',
            'status', 'status_display', 'processing_time_seconds', 'processing_time_formatted',
            'error_message'
        ]
        read_only_fields = [
            'analysis_id', 'analysis_date', 'processing_time_seconds', 'error_message'
        ]
    
    def get_confidence_percentage(self, obj):
        return round(obj.confidence_score * 100, 1) if obj.confidence_score else 0
    
    def get_processing_time_formatted(self, obj):
        if obj.processing_time_seconds:
            if obj.processing_time_seconds < 60:
                return f"{obj.processing_time_seconds}s"
            else:
                minutes = obj.processing_time_seconds // 60
                seconds = obj.processing_time_seconds % 60
                return f"{minutes}m {seconds}s"
        return None

class CosmetologyClientSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CosmetologyClient
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class CosmetologyServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosmetologyService
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CosmetologyProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosmetologyProduct
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CosmetologyAppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    cosmetologist_name = serializers.CharField(source='cosmetologist.username', read_only=True)
    
    class Meta:
        model = CosmetologyAppointment
        fields = '__all__'
        read_only_fields = ['total_amount', 'created_at', 'updated_at']

class TreatmentPlanServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_category = serializers.CharField(source='service.get_category_display', read_only=True)
    
    class Meta:
        model = TreatmentPlanService
        fields = '__all__'

class TreatmentPlanProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_brand = serializers.CharField(source='product.brand', read_only=True)
    
    class Meta:
        model = TreatmentPlanProduct
        fields = '__all__'

class CosmetologyTreatmentPlanSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    cosmetologist_name = serializers.CharField(source='cosmetologist.username', read_only=True)
    plan_services = TreatmentPlanServiceSerializer(source='treatmentplanservice_set', many=True, read_only=True)
    plan_products = TreatmentPlanProductSerializer(source='treatmentplanproduct_set', many=True, read_only=True)
    
    class Meta:
        model = CosmetologyTreatmentPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CosmetologyConsultationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    cosmetologist_name = serializers.CharField(source='cosmetologist.username', read_only=True)
    
    class Meta:
        model = CosmetologyConsultation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CosmetologyProgressSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    treatment_plan_name = serializers.CharField(source='treatment_plan.name', read_only=True)
    
    class Meta:
        model = CosmetologyProgress
        fields = '__all__'
        read_only_fields = ['created_at']

# Simplified serializers for dropdown/selection use
class CosmetologyClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosmetologyClient
        fields = ['id', 'name', 'age', 'gender', 'phone']

class CosmetologyServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosmetologyService
        fields = ['id', 'name', 'category', 'duration', 'price']

class CosmetologyProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosmetologyProduct
        fields = ['id', 'name', 'brand', 'product_type', 'price']

# Dashboard and analytics serializers
class CosmetologyDashboardStatsSerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    active_treatments = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    appointments_today = serializers.IntegerField()
    pending_consultations = serializers.IntegerField()
    top_services = serializers.ListField()
    client_satisfaction_avg = serializers.FloatField()

class AppointmentCalendarSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='service.name')
    start = serializers.DateTimeField(source='appointment_date')
    backgroundColor = serializers.SerializerMethodField()
    
    class Meta:
        model = CosmetologyAppointment
        fields = ['id', 'title', 'start', 'backgroundColor', 'status']
    
    def get_backgroundColor(self, obj):
        color_map = {
            'scheduled': '#ffc107',
            'confirmed': '#28a745',
            'in_progress': '#17a2b8',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
            'no_show': '#e83e8c',
        }
        return color_map.get(obj.status, '#6c757d')


# =============== COSMETIC GYNECOLOGY SERIALIZERS ===============

class CosmeticGynecologyClientSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='cosmetology_client.name', read_only=True)
    client_age = serializers.IntegerField(source='cosmetology_client.age', read_only=True)
    client_email = serializers.EmailField(source='cosmetology_client.email', read_only=True)
    
    class Meta:
        model = CosmeticGynecologyClient
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CosmeticGynecologyTreatmentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    technology_display = serializers.CharField(source='get_technology_used_display', read_only=True)
    
    class Meta:
        model = CosmeticGynecologyTreatment
        fields = '__all__'
        read_only_fields = ['created_at']


class CosmeticGynecologyConsultationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.cosmetology_client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CosmeticGynecologyConsultation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CosmeticGynecologyTreatmentPlanSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.cosmetology_client.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    primary_treatments_details = CosmeticGynecologyTreatmentSerializer(source='primary_treatments', many=True, read_only=True)
    supporting_treatments_details = CosmeticGynecologyTreatmentSerializer(source='supporting_treatments', many=True, read_only=True)
    
    class Meta:
        model = CosmeticGynecologyTreatmentPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CosmeticGynecologyProgressSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='treatment_plan.client.cosmetology_client.name', read_only=True)
    treatment_name = serializers.CharField(source='treatment_performed.name', read_only=True)
    plan_name = serializers.CharField(source='treatment_plan.plan_name', read_only=True)
    
    class Meta:
        model = CosmeticGynecologyProgress
        fields = '__all__'
        read_only_fields = ['created_at']
