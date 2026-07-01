from rest_framework import serializers
from django.db import models
from .models import (
    Institution, RadiologyPatient, RadiologyStudy, 
    RadiologyReport, AIAnalysisResult, DoctorWorkspace, 
    AuditLog, ProcessedDocument
)
from django.contrib.auth.models import User


class InstitutionSerializer(serializers.ModelSerializer):
    """Serializer for Institution model."""
    
    total_patients = serializers.SerializerMethodField()
    total_studies = serializers.SerializerMethodField()
    storage_used_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'code', 'address', 'phone', 'email', 
            'is_active', 'created_at', 'updated_at', 's3_prefix',
            'storage_quota_gb', 'total_patients', 'total_studies', 'storage_used_gb'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 's3_prefix']
    
    def get_total_patients(self, obj):
        return obj.patients.filter(is_active=True).count()
    
    def get_total_studies(self, obj):
        return RadiologyStudy.objects.filter(patient__institution=obj).count()
    
    def get_storage_used_gb(self, obj):
        # Calculate from studies data
        total_mb = RadiologyStudy.objects.filter(
            patient__institution=obj
        ).aggregate(
            total=models.Sum('total_file_size_mb')
        )['total'] or 0
        return round(total_mb / 1024, 2)


class RadiologyPatientSerializer(serializers.ModelSerializer):
    """Serializer for RadiologyPatient model."""
    
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = RadiologyPatient
        fields = [
            'id', 'institution', 'institution_name', 'patient_code',
            'first_name', 'last_name', 's3_patient_prefix', 'is_active',
            'created_at', 'created_by', 'created_by_name', 'last_study_date', 'total_studies'
        ]
        read_only_fields = ['id', 'created_at', 's3_patient_prefix', 'total_studies', 'last_study_date']


class RadiologyStudySerializer(serializers.ModelSerializer):
    """Serializer for RadiologyStudy model."""
    
    patient_name = serializers.SerializerMethodField()
    institution_name = serializers.CharField(source='patient.institution.name', read_only=True)
    ordered_by_name = serializers.CharField(source='ordered_by.get_full_name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    
    class Meta:
        model = RadiologyStudy
        fields = [
            'id', 'patient', 'patient_name', 'institution_name',
            'accession_number', 'study_instance_uid', 'modality', 'body_part',
            'study_description', 'clinical_indication', 'study_date',
            'ordered_by', 'ordered_by_name', 'performed_by', 'performed_by_name',
            'status', 'priority', 's3_study_prefix', 'dicom_file_count',
            'total_file_size_mb', 'has_report', 'has_ai_analysis',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 's3_study_prefix', 
            'dicom_file_count', 'total_file_size_mb', 'has_report', 'has_ai_analysis'
        ]
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class RadiologyReportSerializer(serializers.ModelSerializer):
    """Serializer for RadiologyReport model."""
    
    study_info = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.get_full_name', read_only=True)
    
    class Meta:
        model = RadiologyReport
        fields = [
            'id', 'study', 'study_info', 'report_type', 'status', 'version',
            'created_by', 'created_by_name', 'signed_by', 'signed_by_name', 'signed_at',
            'ai_assisted', 'ai_model_version', 'accuracy_score', 's3_report_key',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 's3_report_key']
    
    def get_study_info(self, obj):
        return {
            'accession_number': obj.study.accession_number,
            'modality': obj.study.modality,
            'body_part': obj.study.body_part,
            'study_date': obj.study.study_date
        }


class AIAnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for AIAnalysisResult model."""
    
    study_info = serializers.SerializerMethodField()
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    
    class Meta:
        model = AIAnalysisResult
        fields = [
            'id', 'study', 'study_info', 'analysis_type', 'ai_model_name',
            'model_version', 'confidence_score', 'processing_time_seconds',
            'has_flags', 'requested_by', 'requested_by_name', 's3_analysis_key',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 's3_analysis_key']
    
    def get_study_info(self, obj):
        return {
            'accession_number': obj.study.accession_number,
            'modality': obj.study.modality,
            'body_part': obj.study.body_part
        }


class DoctorWorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for DoctorWorkspace model."""
    
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    
    class Meta:
        model = DoctorWorkspace
        fields = [
            'id', 'doctor', 'doctor_name', 'institution', 'institution_name',
            'specializations', 's3_workspace_prefix', 'total_reports_created',
            'total_ai_analyses', 'last_activity', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 's3_workspace_prefix',
            'total_reports_created', 'total_ai_analyses', 'last_activity'
        ]


# Legacy serializers (keeping for backward compatibility)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class AnonymizeResponseSerializer(serializers.Serializer):
    original_filename = serializers.CharField(allow_null=True, required=False)
    anonymized_text = serializers.CharField()
    redaction_summary = serializers.JSONField()
    message = serializers.CharField(default="Document anonymized successfully.")

class ReportAnalysisRequestSerializer(serializers.Serializer):
    text_content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)

    def validate(self, data):
        if not data.get('text_content') and not data.get('file'):
            raise serializers.ValidationError("Either text_content or a file must be provided.")
        if data.get('text_content') and data.get('file'):
            raise serializers.ValidationError("Please provide either text_content or a file, not both.")
        return data

class FlaggedIssueSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()
    segment = serializers.CharField()
    suggestion = serializers.CharField()
    startIndex = serializers.IntegerField(required=False, allow_null=True)
    endIndex = serializers.IntegerField(required=False, allow_null=True)

class ReportAnalysisResponseSerializer(serializers.Serializer):
    original_text = serializers.CharField()
    flagged_issues = FlaggedIssueSerializer(many=True)
    accuracy_score = serializers.FloatField()
    error_distribution = serializers.JSONField()
    message = serializers.CharField(default="Report analyzed successfully.")
    original_filename = serializers.CharField(allow_null=True, required=False)


class ProcessedDocumentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    processing_type_display = serializers.CharField(source='get_processing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProcessedDocument
        fields = [
            'id', 'user_email', 'original_filename', 
            'processing_type', 'processing_type_display',
            'status', 'status_display',
            'redacted_item_counts', 'accuracy_score', 'error_distribution',
            'input_preview', 'output_preview',
            'created_at', 'updated_at'
        ]

class MultimodalQueryRequestSerializer(serializers.Serializer):
    report_id = serializers.IntegerField(required=False, help_text="ID of the associated report for context.")
    image = serializers.ImageField(required=False, allow_null=True, help_text="The CXR image file.")
    query = serializers.CharField(required=True, max_length=2000, help_text="The user's question about the image/report.")
    report_context_snippet = serializers.CharField(required=False, allow_blank=True, max_length=4000, help_text="Optional snippet from the report for context.")
    conversation_history_json = serializers.CharField(required=False, allow_blank=True, help_text="JSON string of conversation history e.g., [{'role': 'user', 'content': '...'}, ...]")

class MultimodalQueryResponseSerializer(serializers.Serializer):
    ai_response = serializers.CharField()
    query_received = serializers.CharField()
    image_processed_filename = serializers.CharField(allow_null=True)