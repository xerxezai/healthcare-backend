from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import boto3
import json

from .models import (
    AllopathyHospital, 
    AllopathyPatientS3, 
    AllopathyFile, 
    AllopathyAnalysis, 
    AllopathyMedicalRecord, 
    AllopathyTreatmentPlan
)
from .serializers import (
    AllopathyHospitalSerializer,
    AllopathyPatientS3Serializer,
    AllopathyFileSerializer,
    AllopathyAnalysisSerializer,
    AllopathyMedicalRecordSerializer,
    AllopathyTreatmentPlanSerializer
)

class AllopathyHospitalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Allopathy Hospitals"""
    queryset = AllopathyHospital.objects.all()
    serializer_class = AllopathyHospitalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AllopathyHospital.objects.all()
        hospital_type = self.request.query_params.get('hospital_type', None)
        status = self.request.query_params.get('status', None)
        city = self.request.query_params.get('city', None)
        
        if hospital_type:
            queryset = queryset.filter(hospital_type=hospital_type)
        if status:
            queryset = queryset.filter(status=status)
        if city:
            queryset = queryset.filter(city__icontains=city)
            
        return queryset.order_by('name')
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get hospital statistics"""
        hospital = self.get_object()
        
        stats = {
            'total_patients': hospital.patients.count(),
            'active_patients': hospital.patients.filter(status='active').count(),
            'admitted_patients': hospital.patients.filter(status='admitted').count(),
            'total_files': hospital.files.count(),
            'files_by_category': {},
            'recent_analyses': hospital.analyses.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'bed_occupancy': hospital.patients.filter(status='admitted').count(),
            'bed_capacity': hospital.bed_capacity,
        }
        
        # Files by category
        file_categories = hospital.files.values('category').annotate(count=Count('category'))
        for item in file_categories:
            stats['files_by_category'][item['category']] = item['count']
        
        return Response(stats)

class AllopathyPatientS3ViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Allopathy Patients with S3 integration"""
    queryset = AllopathyPatientS3.objects.all()
    serializer_class = AllopathyPatientS3Serializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AllopathyPatientS3.objects.select_related('hospital')
        
        # Filtering options
        hospital_id = self.request.query_params.get('hospital', None)
        status = self.request.query_params.get('status', None)
        admission_type = self.request.query_params.get('admission_type', None)
        search = self.request.query_params.get('search', None)
        
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        if status:
            queryset = queryset.filter(status=status)
        if admission_type:
            queryset = queryset.filter(admission_type=admission_type)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
            
        return queryset.order_by('-admission_date')
    
    @action(detail=True, methods=['get'])
    def medical_summary(self, request, pk=None):
        """Get comprehensive medical summary for a patient"""
        patient = self.get_object()
        
        summary = {
            'patient_info': AllopathyPatientS3Serializer(patient).data,
            'medical_records': AllopathyMedicalRecordSerializer(
                patient.medical_records.all(), many=True
            ).data,
            'treatment_plans': AllopathyTreatmentPlanSerializer(
                patient.treatment_plans.filter(status='active'), many=True
            ).data,
            'recent_files': AllopathyFileSerializer(
                patient.files.order_by('-upload_date')[:10], many=True
            ).data,
            'recent_analyses': AllopathyAnalysisSerializer(
                patient.analyses.order_by('-created_at')[:5], many=True
            ).data,
        }
        
        return Response(summary)
    
    @action(detail=True, methods=['patch'])
    def update_vital_signs(self, request, pk=None):
        """Update patient vital signs"""
        patient = self.get_object()
        vital_signs = request.data.get('vital_signs', {})
        
        # Validate vital signs data
        required_fields = ['temperature', 'blood_pressure', 'heart_rate', 'respiratory_rate']
        for field in required_fields:
            if field not in vital_signs:
                return Response(
                    {'error': f'Missing required field: {field}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        patient.vital_signs = vital_signs
        patient.save()
        
        return Response({'message': 'Vital signs updated successfully'})

class AllopathyFileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Allopathy Files with S3 operations"""
    queryset = AllopathyFile.objects.all()
    serializer_class = AllopathyFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        queryset = AllopathyFile.objects.select_related('hospital', 'patient', 'uploaded_by')
        
        # Filtering options
        hospital_id = self.request.query_params.get('hospital', None)
        patient_id = self.request.query_params.get('patient', None)
        category = self.request.query_params.get('category', None)
        status = self.request.query_params.get('status', None)
        
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if category:
            queryset = queryset.filter(category=category)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-upload_date')
    
    def perform_create(self, serializer):
        """Handle file upload to S3"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_download_url(self, request, pk=None):
        """Generate a presigned URL for file download"""
        file_obj = self.get_object()
        
        try:
            s3_client = boto3.client('s3')
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': file_obj.s3_bucket, 'Key': file_obj.s3_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return Response({'download_url': download_url})
        except Exception as e:
            return Response(
                {'error': f'Failed to generate download URL: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def storage_analytics(self, request):
        """Get storage analytics for all files"""
        total_files = AllopathyFile.objects.count()
        total_size = AllopathyFile.objects.aggregate(
            total_size=Sum('file_size')
        )['total_size'] or 0
        
        # Files by category
        category_stats = AllopathyFile.objects.values('category').annotate(
            count=Count('id'),
            total_size=models.Sum('file_size')
        )
        
        # Files by status
        status_stats = AllopathyFile.objects.values('status').annotate(
            count=Count('id')
        )
        
        analytics = {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024**3), 2),
            'category_breakdown': list(category_stats),
            'status_breakdown': list(status_stats),
        }
        
        return Response(analytics)

class AllopathyAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI Analysis of medical data"""
    queryset = AllopathyAnalysis.objects.all()
    serializer_class = AllopathyAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AllopathyAnalysis.objects.select_related('hospital', 'patient', 'file')
        
        # Filtering options
        analysis_type = self.request.query_params.get('analysis_type', None)
        status = self.request.query_params.get('status', None)
        patient_id = self.request.query_params.get('patient', None)
        confidence_min = self.request.query_params.get('confidence_min', None)
        
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
        if status:
            queryset = queryset.filter(status=status)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if confidence_min:
            try:
                queryset = queryset.filter(confidence_score__gte=float(confidence_min))
            except ValueError:
                pass
                
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve_analysis(self, request, pk=None):
        """Approve an analysis result"""
        analysis = self.get_object()
        review_notes = request.data.get('review_notes', '')
        
        analysis.status = 'approved'
        analysis.reviewed_by = request.user
        analysis.review_notes = review_notes
        analysis.save()
        
        return Response({'message': 'Analysis approved successfully'})
    
    @action(detail=False, methods=['post'])
    def batch_process(self, request):
        """Trigger batch processing of pending analyses"""
        pending_analyses = AllopathyAnalysis.objects.filter(status='pending')
        
        # Update status to processing
        updated_count = pending_analyses.update(status='processing')
        
        # Here you would trigger your AI processing pipeline
        # For now, we'll just return the count
        
        return Response({
            'message': f'Started processing {updated_count} analyses',
            'updated_count': updated_count
        })

class AllopathyMedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Medical Records"""
    queryset = AllopathyMedicalRecord.objects.all()
    serializer_class = AllopathyMedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AllopathyMedicalRecord.objects.select_related('patient')
        
        # Filtering options
        patient_id = self.request.query_params.get('patient', None)
        status = self.request.query_params.get('status', None)
        physician = self.request.query_params.get('physician', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if status:
            queryset = queryset.filter(status=status)
        if physician:
            queryset = queryset.filter(attending_physician__icontains=physician)
        if date_from:
            queryset = queryset.filter(admission_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(admission_date__lte=date_to)
            
        return queryset.order_by('-admission_date')

class AllopathyTreatmentPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Treatment Plans"""
    queryset = AllopathyTreatmentPlan.objects.all()
    serializer_class = AllopathyTreatmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AllopathyTreatmentPlan.objects.select_related('patient', 'medical_record')
        
        # Filtering options
        patient_id = self.request.query_params.get('patient', None)
        status = self.request.query_params.get('status', None)
        priority = self.request.query_params.get('priority', None)
        prescribed_by = self.request.query_params.get('prescribed_by', None)
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if prescribed_by:
            queryset = queryset.filter(prescribed_by__icontains=prescribed_by)
            
        return queryset.order_by('-plan_date')
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update treatment plan status"""
        treatment_plan = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(AllopathyTreatmentPlan.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        treatment_plan.status = new_status
        if notes:
            treatment_plan.notes = notes
        treatment_plan.save()
        
        return Response({'message': 'Treatment plan status updated successfully'})
