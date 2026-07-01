from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging
import json
from datetime import datetime
from typing import Dict, Any

from .models import (
    Institution, RadiologyPatient, RadiologyStudy, 
    RadiologyReport, AIAnalysisResult, DoctorWorkspace, AuditLog
)
from .services.radiology_s3_manager import radiology_s3_manager
from .serializers import (
    InstitutionSerializer, RadiologyPatientSerializer, 
    RadiologyStudySerializer, RadiologyReportSerializer,
    AIAnalysisResultSerializer, DoctorWorkspaceSerializer
)

logger = logging.getLogger(__name__)


def log_audit_action(user, institution, action, resource_type, resource_id, request, details=None):
    """Helper function to log audit actions."""
    try:
        AuditLog.objects.create(
            user=user,
            institution=institution,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=details or {}
        )
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_patient(request):
    """Create a new patient with S3 storage setup."""
    try:
        data = request.data
        institution_id = data.get('institution_id')
        
        if not institution_id:
            return Response(
                {'error': 'Institution ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        institution = get_object_or_404(Institution, id=institution_id)
        
        # Create patient record in PostgreSQL
        patient_data = {
            'institution': institution,
            'patient_code': data.get('patient_code'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'created_by': request.user
        }
        
        patient = RadiologyPatient.objects.create(**patient_data)
        
        # Create patient profile in S3
        s3_patient_data = {
            'patient_code': data.get('patient_code'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'dob': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'phone': data.get('phone'),
            'email': data.get('email'),
            'address': data.get('address'),
            'emergency_contact': data.get('emergency_contact'),
            'medical_history': data.get('medical_history', []),
            'allergies': data.get('allergies', []),
            'created_by': request.user.id
        }
        
        patient_s3_id, error = radiology_s3_manager.create_patient_profile(
            str(institution.id), s3_patient_data
        )
        
        if error:
            patient.delete()  # Rollback
            return Response(
                {'error': f'Failed to create patient in S3: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update patient with S3 reference
        patient.s3_patient_prefix = radiology_s3_manager.get_patient_prefix(
            str(institution.id), patient_s3_id
        )
        patient.save()
        
        # Log audit
        log_audit_action(
            request.user, institution, 'create', 'patient', 
            patient.id, request, {'patient_code': patient.patient_code}
        )
        
        serializer = RadiologyPatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        return Response(
            {'error': 'Failed to create patient'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_study(request):
    """Create a new imaging study."""
    try:
        data = request.data
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'Patient ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient = get_object_or_404(RadiologyPatient, id=patient_id)
        
        # Create study record in PostgreSQL
        study_data = {
            'patient': patient,
            'accession_number': data.get('accession_number'),
            'study_instance_uid': data.get('study_instance_uid', ''),
            'modality': data.get('modality'),
            'body_part': data.get('body_part'),
            'study_description': data.get('study_description'),
            'clinical_indication': data.get('clinical_indication', ''),
            'study_date': data.get('study_date'),
            'ordered_by': request.user,
            'priority': data.get('priority', 'routine')
        }
        
        study = RadiologyStudy.objects.create(**study_data)
        
        # Create study in S3
        s3_study_data = {
            'study_type': data.get('modality'),
            'modality': data.get('modality'),
            'body_part': data.get('body_part'),
            'description': data.get('study_description'),
            'clinical_indication': data.get('clinical_indication'),
            'study_date': data.get('study_date'),
            'ordered_by': request.user.id,
            'priority': data.get('priority', 'routine')
        }
        
        # Extract patient S3 ID from prefix
        patient_s3_id = patient.s3_patient_prefix.split('/')[-2]
        
        study_s3_id, error = radiology_s3_manager.create_study(
            str(patient.institution.id), patient_s3_id, s3_study_data
        )
        
        if error:
            study.delete()  # Rollback
            return Response(
                {'error': f'Failed to create study in S3: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update study with S3 reference
        study.s3_study_prefix = radiology_s3_manager.get_study_prefix(
            str(patient.institution.id), patient_s3_id, study_s3_id
        )
        study.save()
        
        # Update patient study count
        patient.total_studies += 1
        patient.last_study_date = study.study_date
        patient.save()
        
        # Log audit
        log_audit_action(
            request.user, patient.institution, 'create', 'study', 
            study.id, request, {'accession_number': study.accession_number}
        )
        
        serializer = RadiologyStudySerializer(study)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating study: {e}")
        return Response(
            {'error': 'Failed to create study'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_dicom(request):
    """Upload DICOM file to a study."""
    try:
        study_id = request.data.get('study_id')
        uploaded_file = request.FILES.get('dicom_file')
        
        if not study_id or not uploaded_file:
            return Response(
                {'error': 'Study ID and DICOM file are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        study = get_object_or_404(RadiologyStudy, id=study_id)
        
        # Extract S3 path components from study prefix
        prefix_parts = study.s3_study_prefix.strip('/').split('/')
        institution_id = prefix_parts[2]  # radiology/institutions/{id}/...
        patient_s3_id = prefix_parts[4]   # .../patients/{id}/...
        study_s3_id = prefix_parts[6]     # .../studies/{id}/
        
        # Upload to S3
        file_key, error = radiology_s3_manager.upload_dicom_file(
            institution_id, patient_s3_id, study_s3_id,
            uploaded_file, uploaded_file.name
        )
        
        if error:
            return Response(
                {'error': f'Failed to upload DICOM: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update study metadata
        study.dicom_file_count += 1
        study.total_file_size_mb += uploaded_file.size / (1024 * 1024)
        study.status = 'in_progress'
        study.save()
        
        # Log audit
        log_audit_action(
            request.user, study.patient.institution, 'upload', 'dicom', 
            study.id, request, {'filename': uploaded_file.name, 'size': uploaded_file.size}
        )
        
        return Response({
            'message': 'DICOM file uploaded successfully',
            'file_key': file_key,
            'study_status': study.status,
            'file_count': study.dicom_file_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error uploading DICOM: {e}")
        return Response(
            {'error': 'Failed to upload DICOM file'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request):
    """Create a radiology report."""
    try:
        data = request.data
        study_id = data.get('study_id')
        
        if not study_id:
            return Response(
                {'error': 'Study ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        study = get_object_or_404(RadiologyStudy, id=study_id)
        
        # Create report record in PostgreSQL
        report = RadiologyReport.objects.create(
            study=study,
            report_type=data.get('report_type', 'radiology'),
            status=data.get('status', 'draft'),
            created_by=request.user,
            ai_assisted=data.get('ai_assisted', False),
            ai_model_version=data.get('ai_model_version', ''),
            accuracy_score=data.get('accuracy_score')
        )
        
        # Prepare report data for S3
        report_data = {
            'findings': data.get('findings', ''),
            'impression': data.get('impression', ''),
            'recommendations': data.get('recommendations', ''),
            'technique': data.get('technique', ''),
            'comparison': data.get('comparison', ''),
            'created_by': request.user.id,
            'status': data.get('status', 'draft'),
            'ai_assisted': data.get('ai_assisted', False),
            'accuracy_score': data.get('accuracy_score')
        }
        
        # Extract S3 path components
        prefix_parts = study.s3_study_prefix.strip('/').split('/')
        institution_id = prefix_parts[2]
        patient_s3_id = prefix_parts[4]
        study_s3_id = prefix_parts[6]
        
        # Upload report to S3
        report_key, error = radiology_s3_manager.upload_report(
            institution_id, patient_s3_id, study_s3_id,
            report_data, data.get('report_type', 'radiology')
        )
        
        if error:
            report.delete()  # Rollback
            return Response(
                {'error': f'Failed to create report in S3: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update report with S3 reference
        report.s3_report_key = report_key
        report.save()
        
        # Update study status
        study.has_report = True
        if study.status == 'completed':
            study.status = 'reported'
        study.save()
        
        # Log audit
        log_audit_action(
            request.user, study.patient.institution, 'create', 'report', 
            report.id, request, {'study': study.accession_number}
        )
        
        serializer = RadiologyReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return Response(
            {'error': 'Failed to create report'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_ai_analysis(request):
    """Store AI analysis results."""
    try:
        data = request.data
        study_id = data.get('study_id')
        
        if not study_id:
            return Response(
                {'error': 'Study ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        study = get_object_or_404(RadiologyStudy, id=study_id)
        
        # Create AI analysis record in PostgreSQL
        ai_analysis = AIAnalysisResult.objects.create(
            study=study,
            analysis_type=data.get('analysis_type'),
            ai_model_name=data.get('ai_model_name'),
            model_version=data.get('model_version'),
            confidence_score=data.get('confidence_score'),
            processing_time_seconds=data.get('processing_time'),
            has_flags=data.get('has_flags', False),
            requested_by=request.user
        )
        
        # Prepare analysis data for S3
        analysis_data = {
            'model_version': data.get('model_version'),
            'confidence_score': data.get('confidence_score'),
            'processing_time': data.get('processing_time'),
            'results': data.get('results', {}),
            'recommendations': data.get('recommendations', []),
            'flags': data.get('flags', []),
            'metadata': data.get('metadata', {}),
            'input_parameters': data.get('input_parameters', {}),
            'output_summary': data.get('output_summary', '')
        }
        
        # Extract S3 path components
        prefix_parts = study.s3_study_prefix.strip('/').split('/')
        institution_id = prefix_parts[2]
        patient_s3_id = prefix_parts[4]
        study_s3_id = prefix_parts[6]
        
        # Store analysis in S3
        analysis_key, error = radiology_s3_manager.store_ai_analysis_result(
            institution_id, patient_s3_id, study_s3_id,
            analysis_data, data.get('analysis_type')
        )
        
        if error:
            ai_analysis.delete()  # Rollback
            return Response(
                {'error': f'Failed to store AI analysis in S3: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update analysis with S3 reference
        ai_analysis.s3_analysis_key = analysis_key
        ai_analysis.save()
        
        # Update study status
        study.has_ai_analysis = True
        study.save()
        
        # Update doctor workspace statistics
        try:
            workspace = DoctorWorkspace.objects.get(
                doctor=request.user, 
                institution=study.patient.institution
            )
            workspace.total_ai_analyses += 1
            workspace.save()
        except DoctorWorkspace.DoesNotExist:
            pass
        
        # Log audit
        log_audit_action(
            request.user, study.patient.institution, 'create', 'ai_analysis', 
            ai_analysis.id, request, {
                'analysis_type': ai_analysis.analysis_type,
                'study': study.accession_number
            }
        )
        
        serializer = AIAnalysisResultSerializer(ai_analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error storing AI analysis: {e}")
        return Response(
            {'error': 'Failed to store AI analysis'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_studies(request, patient_id):
    """Get all studies for a patient."""
    try:
        patient = get_object_or_404(RadiologyPatient, id=patient_id)
        
        # Check if user has access to this patient's institution
        # Add proper permission checking here
        
        studies = RadiologyStudy.objects.filter(patient=patient).order_by('-study_date')
        
        # Log audit
        log_audit_action(
            request.user, patient.institution, 'read', 'patient_studies', 
            patient.id, request
        )
        
        serializer = RadiologyStudySerializer(studies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving patient studies: {e}")
        return Response(
            {'error': 'Failed to retrieve patient studies'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_study_details(request, study_id):
    """Get complete study details including S3 content."""
    try:
        study = get_object_or_404(RadiologyStudy, id=study_id)
        
        # Extract S3 path components
        prefix_parts = study.s3_study_prefix.strip('/').split('/')
        institution_id = prefix_parts[2]
        patient_s3_id = prefix_parts[4]
        study_s3_id = prefix_parts[6]
        
        # Get detailed study data from S3
        study_details, error = radiology_s3_manager.get_study_details(
            institution_id, patient_s3_id, study_s3_id
        )
        
        if error:
            return Response(
                {'error': f'Failed to retrieve study details: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Combine PostgreSQL and S3 data
        response_data = {
            'study_info': RadiologyStudySerializer(study).data,
            'study_details': study_details,
            'reports': RadiologyReportSerializer(study.reports.all(), many=True).data,
            'ai_analyses': AIAnalysisResultSerializer(study.ai_analyses.all(), many=True).data
        }
        
        # Log audit
        log_audit_action(
            request.user, study.patient.institution, 'read', 'study_details', 
            study.id, request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving study details: {e}")
        return Response(
            {'error': 'Failed to retrieve study details'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_studies(request):
    """Search studies across the institution."""
    try:
        data = request.data
        institution_id = data.get('institution_id')
        
        if not institution_id:
            return Response(
                {'error': 'Institution ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        institution = get_object_or_404(Institution, id=institution_id)
        
        # Search criteria
        search_criteria = {
            'modality': data.get('modality'),
            'body_part': data.get('body_part'),
            'study_date_from': data.get('study_date_from'),
            'study_date_to': data.get('study_date_to'),
            'patient_name': data.get('patient_name'),
            'accession_number': data.get('accession_number')
        }
        
        # Remove None values
        search_criteria = {k: v for k, v in search_criteria.items() if v is not None}
        
        # Search in S3 (for advanced search)
        s3_results, error = radiology_s3_manager.search_studies(
            str(institution.id), search_criteria, limit=data.get('limit', 100)
        )
        
        if error:
            return Response(
                {'error': f'Search failed: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Also search in PostgreSQL for quick filtering
        queryset = RadiologyStudy.objects.filter(patient__institution=institution)
        
        if search_criteria.get('modality'):
            queryset = queryset.filter(modality=search_criteria['modality'])
        if search_criteria.get('body_part'):
            queryset = queryset.filter(body_part__icontains=search_criteria['body_part'])
        if search_criteria.get('accession_number'):
            queryset = queryset.filter(accession_number__icontains=search_criteria['accession_number'])
        
        pg_studies = RadiologyStudySerializer(queryset[:50], many=True).data
        
        # Log audit
        log_audit_action(
            request.user, institution, 'read', 'search_studies', 
            institution.id, request, {'criteria': search_criteria}
        )
        
        return Response({
            'postgresql_results': pg_studies,
            's3_results': s3_results,
            'total_s3_results': len(s3_results)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error searching studies: {e}")
        return Response(
            {'error': 'Search failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_institution_analytics(request, institution_id):
    """Get analytics data for the institution."""
    try:
        institution = get_object_or_404(Institution, id=institution_id)
        
        # Get analytics from S3
        analytics_data, error = radiology_s3_manager.get_analytics_data(
            str(institution.id)
        )
        
        if error:
            return Response(
                {'error': f'Failed to retrieve analytics: {error}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Add PostgreSQL analytics
        pg_analytics = {
            'total_patients': RadiologyPatient.objects.filter(institution=institution).count(),
            'total_studies': RadiologyStudy.objects.filter(patient__institution=institution).count(),
            'total_reports': RadiologyReport.objects.filter(study__patient__institution=institution).count(),
            'total_ai_analyses': AIAnalysisResult.objects.filter(study__patient__institution=institution).count(),
            'active_doctors': DoctorWorkspace.objects.filter(institution=institution).count()
        }
        
        combined_analytics = {
            'postgresql_data': pg_analytics,
            's3_data': analytics_data,
            'institution_info': InstitutionSerializer(institution).data
        }
        
        # Log audit
        log_audit_action(
            request.user, institution, 'read', 'analytics', 
            institution.id, request
        )
        
        return Response(combined_analytics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving analytics: {e}")
        return Response(
            {'error': 'Failed to retrieve analytics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ViewSet classes for REST API endpoints
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class InstitutionViewSet(viewsets.ModelViewSet):
    """ViewSet for Institution model."""
    
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class RadiologyPatientViewSet(viewsets.ModelViewSet):
    """ViewSet for RadiologyPatient model."""
    
    queryset = RadiologyPatient.objects.all()
    serializer_class = RadiologyPatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['institution', 'is_active']
    search_fields = ['first_name', 'last_name', 'patient_code']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['first_name', 'last_name']


class RadiologyStudyViewSet(viewsets.ModelViewSet):
    """ViewSet for RadiologyStudy model."""
    
    queryset = RadiologyStudy.objects.all()
    serializer_class = RadiologyStudySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'modality', 'status', 'priority', 'body_part']
    search_fields = ['accession_number', 'study_description', 'clinical_indication']
    ordering_fields = ['study_date', 'created_at', 'accession_number']
    ordering = ['-study_date']


class RadiologyReportViewSet(viewsets.ModelViewSet):
    """ViewSet for RadiologyReport model."""
    
    queryset = RadiologyReport.objects.all()
    serializer_class = RadiologyReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['study', 'report_type', 'status', 'ai_assisted']
    search_fields = ['study__accession_number']
    ordering_fields = ['created_at', 'signed_at']
    ordering = ['-created_at']


class AIAnalysisResultViewSet(viewsets.ModelViewSet):
    """ViewSet for AIAnalysisResult model."""
    
    queryset = AIAnalysisResult.objects.all()
    serializer_class = AIAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['study', 'analysis_type', 'ai_model_name', 'has_flags']
    search_fields = ['study__accession_number', 'ai_model_name']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']


class DoctorWorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for DoctorWorkspace model."""
    
    queryset = DoctorWorkspace.objects.all()
    serializer_class = DoctorWorkspaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['doctor', 'institution']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specializations']
    ordering_fields = ['last_activity', 'created_at']
    ordering = ['-last_activity']


# Missing function references for URL patterns
def search_patients(request):
    """Search patients function - placeholder for now."""
    return Response({'message': 'Patient search endpoint'})

def get_study_reports(request, study_id):
    """Get study reports function - placeholder for now."""
    return Response({'message': 'Study reports endpoint'})

def get_analytics_dashboard(request):
    """Get analytics dashboard function - placeholder for now.""" 
    return Response({'message': 'Analytics dashboard endpoint'})
