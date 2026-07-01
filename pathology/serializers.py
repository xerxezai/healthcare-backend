from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PathologyDepartment, PathologyTest, Patient, PathologyOrder,
    PathologyOrderTest, Specimen, PathologyReport, DigitalSlide,
    PathologyQualityControl
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer for pathologist information"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PathologyDepartmentSerializer(serializers.ModelSerializer):
    """Pathology Department serializer"""
    head_pathologist_details = UserSerializer(source='head_pathologist', read_only=True)
    
    class Meta:
        model = PathologyDepartment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PathologyTestSerializer(serializers.ModelSerializer):
    """Pathology Test serializer"""
    class Meta:
        model = PathologyTest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PatientSerializer(serializers.ModelSerializer):
    """Patient serializer"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SpecimenSerializer(serializers.ModelSerializer):
    """Specimen serializer"""
    collected_by_details = UserSerializer(source='collected_by', read_only=True)
    
    class Meta:
        model = Specimen
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PathologyOrderTestSerializer(serializers.ModelSerializer):
    """Pathology Order Test serializer"""
    test_details = PathologyTestSerializer(source='test', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = PathologyOrderTest
        fields = '__all__'


class PathologyOrderSerializer(serializers.ModelSerializer):
    """Pathology Order serializer"""
    patient_details = PatientSerializer(source='patient', read_only=True)
    ordering_physician_details = UserSerializer(source='ordering_physician', read_only=True)
    department_details = PathologyDepartmentSerializer(source='department', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    order_tests = PathologyOrderTestSerializer(source='pathologyordertest_set', many=True, read_only=True)
    specimens = SpecimenSerializer(many=True, read_only=True)
    
    class Meta:
        model = PathologyOrder
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'order_id']

    def create(self, validated_data):
        # Generate unique order ID
        import uuid
        validated_data['order_id'] = f"PATH-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)


class DigitalSlideSerializer(serializers.ModelSerializer):
    """Digital Slide serializer"""
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = DigitalSlide
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'slide_id']


class PathologyReportSerializer(serializers.ModelSerializer):
    """Pathology Report serializer"""
    pathologist_details = UserSerializer(source='pathologist', read_only=True)
    order_test_details = PathologyOrderTestSerializer(source='order_test', read_only=True)
    specimen_details = SpecimenSerializer(source='specimen', read_only=True)
    slides = DigitalSlideSerializer(many=True, read_only=True)
    
    class Meta:
        model = PathologyReport
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'report_id']

    def create(self, validated_data):
        # Generate unique report ID
        import uuid
        validated_data['report_id'] = f"RPT-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)


class PathologyQualityControlSerializer(serializers.ModelSerializer):
    """Quality Control serializer"""
    performed_by_details = UserSerializer(source='performed_by', read_only=True)
    
    class Meta:
        model = PathologyQualityControl
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'qc_id']

    def create(self, validated_data):
        # Generate unique QC ID
        import uuid
        validated_data['qc_id'] = f"QC-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)


# Dashboard and Analytics Serializers
class PathologyDashboardSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    total_tests = serializers.IntegerField()
    recent_orders = PathologyOrderSerializer(many=True)
    recent_reports = PathologyReportSerializer(many=True)
    critical_results = serializers.IntegerField()
    turnaround_time_avg = serializers.FloatField()


class TestStatisticsSerializer(serializers.Serializer):
    """Test statistics serializer"""
    test_name = serializers.CharField()
    test_count = serializers.IntegerField()
    normal_results = serializers.IntegerField()
    abnormal_results = serializers.IntegerField()
    critical_results = serializers.IntegerField()
    avg_turnaround_time = serializers.FloatField()


class PathologyAnalyticsSerializer(serializers.Serializer):
    """Analytics data serializer"""
    monthly_test_volume = serializers.DictField()
    test_category_distribution = serializers.DictField()
    turnaround_time_trends = serializers.DictField()
    quality_metrics = serializers.DictField()
    department_performance = serializers.DictField()
    pathologist_workload = serializers.DictField()


# S3 Data Management Serializers

from .models import PathologyLaboratory, PathologyPatient, PathologySpecimen, PathologyFile, PathologyAnalysis


class PathologyLaboratorySerializer(serializers.ModelSerializer):
    """Pathology Laboratory serializer for S3 data management"""
    total_patients = serializers.SerializerMethodField()
    total_specimens = serializers.SerializerMethodField()
    total_files = serializers.SerializerMethodField()
    
    class Meta:
        model = PathologyLaboratory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_patients(self, obj):
        return obj.patients.count()
    
    def get_total_specimens(self, obj):
        return obj.specimens.count()
    
    def get_total_files(self, obj):
        return obj.files.count()


class PathologyPatientSerializer(serializers.ModelSerializer):
    """Pathology Patient serializer for S3 data management"""
    laboratory_details = PathologyLaboratorySerializer(source='laboratory', read_only=True)
    full_name = serializers.ReadOnlyField()
    total_specimens = serializers.SerializerMethodField()
    total_files = serializers.SerializerMethodField()
    
    class Meta:
        model = PathologyPatient
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_specimens(self, obj):
        return obj.specimens.count()
    
    def get_total_files(self, obj):
        return obj.files.count()


class PathologySpecimenSerializer(serializers.ModelSerializer):
    """Pathology Specimen serializer"""
    patient_details = PathologyPatientSerializer(source='patient', read_only=True)
    laboratory_details = PathologyLaboratorySerializer(source='laboratory', read_only=True)
    total_files = serializers.SerializerMethodField()
    
    class Meta:
        model = PathologySpecimen
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_files(self, obj):
        return obj.files.count()


class PathologyFileSerializer(serializers.ModelSerializer):
    """Pathology File serializer for S3 management"""
    laboratory_details = PathologyLaboratorySerializer(source='laboratory', read_only=True)
    patient_details = PathologyPatientSerializer(source='patient', read_only=True)
    specimen_details = PathologySpecimenSerializer(source='specimen', read_only=True)
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)
    size_formatted = serializers.SerializerMethodField()
    total_analyses = serializers.SerializerMethodField()
    
    class Meta:
        model = PathologyFile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 's3_key', 's3_url']
    
    def get_size_formatted(self, obj):
        """Format file size in human readable format"""
        if obj.size:
            if obj.size < 1024:
                return f"{obj.size} B"
            elif obj.size < 1024 * 1024:
                return f"{obj.size / 1024:.1f} KB"
            elif obj.size < 1024 * 1024 * 1024:
                return f"{obj.size / (1024 * 1024):.1f} MB"
            else:
                return f"{obj.size / (1024 * 1024 * 1024):.1f} GB"
        return "0 B"
    
    def get_total_analyses(self, obj):
        return obj.analyses.count()


class PathologyAnalysisSerializer(serializers.ModelSerializer):
    """Pathology Analysis serializer for AI/ML results"""
    file_details = PathologyFileSerializer(source='file', read_only=True)
    reviewed_by_details = UserSerializer(source='reviewed_by', read_only=True)
    processing_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = PathologyAnalysis
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_processing_time_formatted(self, obj):
        """Format processing time in human readable format"""
        if obj.processing_time:
            total_seconds = obj.processing_time.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f} seconds"
            elif total_seconds < 3600:
                return f"{total_seconds / 60:.1f} minutes"
            else:
                return f"{total_seconds / 3600:.1f} hours"
        return "N/A"


class PathologyS3AnalyticsSerializer(serializers.Serializer):
    """S3 Storage Analytics serializer"""
    total_files = serializers.IntegerField()
    total_size_bytes = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    file_counts_by_type = serializers.DictField()
    recent_uploads_last_week = serializers.IntegerField()
    total_laboratories = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    total_specimens = serializers.IntegerField()
    bucket_name = serializers.CharField()
    region = serializers.CharField()


class PathologyReportSerializer(serializers.Serializer):
    """Pathology Report serializer"""
    patient_info = serializers.DictField()
    analyses = serializers.ListField()
    summary = serializers.DictField()
    generated_at = serializers.CharField()
