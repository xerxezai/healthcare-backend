from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncMonth, TruncDay
import json

from .models import (
    PathologyDepartment, PathologyTest, Patient, PathologyOrder,
    PathologyOrderTest, Specimen, PathologyReport, DigitalSlide,
    PathologyQualityControl
)
from .serializers import (
    PathologyDepartmentSerializer, PathologyTestSerializer, PatientSerializer,
    PathologyOrderSerializer, PathologyOrderTestSerializer, SpecimenSerializer,
    PathologyReportSerializer, DigitalSlideSerializer, PathologyQualityControlSerializer,
    PathologyDashboardSerializer, TestStatisticsSerializer, PathologyAnalyticsSerializer
)


class PathologyDepartmentViewSet(viewsets.ModelViewSet):
    """Pathology Department management"""
    queryset = PathologyDepartment.objects.all()
    serializer_class = PathologyDepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyDepartment.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class PathologyTestViewSet(viewsets.ModelViewSet):
    """Pathology Test management"""
    queryset = PathologyTest.objects.all()
    serializer_class = PathologyTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyTest.objects.all()
        category = self.request.query_params.get('category', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available test categories"""
        categories = PathologyTest.TEST_CATEGORIES
        return Response(categories)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular tests"""
        popular_tests = PathologyTest.objects.annotate(
            order_count=Count('pathologyordertest')
        ).order_by('-order_count')[:10]
        
        serializer = self.get_serializer(popular_tests, many=True)
        return Response(serializer.data)


class PatientViewSet(viewsets.ModelViewSet):
    """Patient management for pathology"""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Patient.objects.all()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(medical_record_number__icontains=search)
            )
        
        return queryset

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get all pathology orders for a patient"""
        patient = self.get_object()
        orders = PathologyOrder.objects.filter(patient=patient)
        serializer = PathologyOrderSerializer(orders, many=True)
        return Response(serializer.data)


class PathologyOrderViewSet(viewsets.ModelViewSet):
    """Pathology Order management"""
    queryset = PathologyOrder.objects.all()
    serializer_class = PathologyOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyOrder.objects.select_related(
            'patient', 'ordering_physician', 'department', 'created_by'
        ).prefetch_related('tests', 'specimens')
        
        status_filter = self.request.query_params.get('status', None)
        priority = self.request.query_params.get('priority', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority:
            queryset = queryset.filter(priority=priority)
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_tests(self, request, pk=None):
        """Add tests to an existing order"""
        order = self.get_object()
        test_ids = request.data.get('test_ids', [])
        
        for test_id in test_ids:
            try:
                test = PathologyTest.objects.get(id=test_id)
                PathologyOrderTest.objects.get_or_create(
                    order=order,
                    test=test,
                    defaults={'cost': test.cost}
                )
            except PathologyTest.DoesNotExist:
                continue
        
        # Recalculate total cost
        total_cost = sum(ot.cost for ot in order.pathologyordertest_set.all())
        order.total_cost = total_cost
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(PathologyOrder.ORDER_STATUS):
            order.status = new_status
            
            # Auto-update timestamps based on status
            if new_status == 'collected':
                order.collection_date = timezone.now()
            elif new_status == 'completed':
                order.expected_completion = timezone.now()
            
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid status'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class SpecimenViewSet(viewsets.ModelViewSet):
    """Specimen management"""
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Specimen.objects.select_related('order', 'collected_by')
        
        status_filter = self.request.query_params.get('status', None)
        specimen_type = self.request.query_params.get('type', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if specimen_type:
            queryset = queryset.filter(specimen_type=specimen_type)
        
        return queryset

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update specimen status"""
        specimen = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Specimen.SPECIMEN_STATUS):
            specimen.status = new_status
            
            # Auto-update timestamps
            if new_status == 'received':
                specimen.received_datetime = timezone.now()
            
            specimen.save()
            serializer = self.get_serializer(specimen)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid status'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class PathologyReportViewSet(viewsets.ModelViewSet):
    """Pathology Report management"""
    queryset = PathologyReport.objects.all()
    serializer_class = PathologyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyReport.objects.select_related(
            'pathologist', 'order_test__test', 'specimen'
        ).prefetch_related('slides')
        
        status_filter = self.request.query_params.get('status', None)
        result_status = self.request.query_params.get('result_status', None)
        pathologist_id = self.request.query_params.get('pathologist', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if result_status:
            queryset = queryset.filter(result_status=result_status)
        if pathologist_id:
            queryset = queryset.filter(pathologist_id=pathologist_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(pathologist=self.request.user)

    @action(detail=True, methods=['patch'])
    def finalize(self, request, pk=None):
        """Finalize a pathology report"""
        report = self.get_object()
        
        if report.status == 'reviewed':
            report.status = 'finalized'
            report.finalized_at = timezone.now()
            report.save()
            
            # Update order test status
            report.order_test.status = 'completed'
            report.order_test.completed_at = timezone.now()
            report.order_test.save()
            
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Report must be reviewed before finalizing'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def critical_results(self, request):
        """Get critical results requiring immediate attention"""
        critical_reports = PathologyReport.objects.filter(
            result_status='critical',
            status='finalized'
        ).order_by('-finalized_at')
        
        serializer = self.get_serializer(critical_reports, many=True)
        return Response(serializer.data)


class DigitalSlideViewSet(viewsets.ModelViewSet):
    """Digital Slide management"""
    queryset = DigitalSlide.objects.all()
    serializer_class = DigitalSlideSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_annotation(self, request, pk=None):
        """Add annotation to digital slide"""
        slide = self.get_object()
        annotation = request.data.get('annotation')
        
        if annotation:
            slide.annotations.append(annotation)
            slide.save()
            
        serializer = self.get_serializer(slide)
        return Response(serializer.data)


class PathologyQualityControlViewSet(viewsets.ModelViewSet):
    """Quality Control management"""
    queryset = PathologyQualityControl.objects.all()
    serializer_class = PathologyQualityControlSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get QC items due soon"""
        next_week = timezone.now() + timedelta(days=7)
        due_qc = PathologyQualityControl.objects.filter(
            next_due_date__lte=next_week,
            next_due_date__gte=timezone.now()
        ).order_by('next_due_date')
        
        serializer = self.get_serializer(due_qc, many=True)
        return Response(serializer.data)


# Dashboard and Analytics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pathology_dashboard(request):
    """Get pathology dashboard statistics"""
    # Basic counts
    total_orders = PathologyOrder.objects.count()
    pending_orders = PathologyOrder.objects.filter(status='pending').count()
    completed_orders = PathologyOrder.objects.filter(status='completed').count()
    total_patients = Patient.objects.count()
    total_tests = PathologyTest.objects.filter(is_active=True).count()
    
    # Recent data
    recent_orders = PathologyOrder.objects.order_by('-created_at')[:5]
    recent_reports = PathologyReport.objects.filter(
        status='finalized'
    ).order_by('-finalized_at')[:5]
    
    # Critical results count
    critical_results = PathologyReport.objects.filter(
        result_status='critical',
        status='finalized'
    ).count()
    
    # Average turnaround time (in hours)
    completed_tests = PathologyOrderTest.objects.filter(
        status='completed',
        started_at__isnull=False,
        completed_at__isnull=False
    )
    
    turnaround_times = []
    for test in completed_tests:
        if test.started_at and test.completed_at:
            delta = test.completed_at - test.started_at
            turnaround_times.append(delta.total_seconds() / 3600)  # Convert to hours
    
    avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
    
    dashboard_data = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_patients': total_patients,
        'total_tests': total_tests,
        'recent_orders': PathologyOrderSerializer(recent_orders, many=True).data,
        'recent_reports': PathologyReportSerializer(recent_reports, many=True).data,
        'critical_results': critical_results,
        'turnaround_time_avg': round(avg_turnaround, 2)
    }
    
    serializer = PathologyDashboardSerializer(dashboard_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pathology_analytics(request):
    """Get detailed pathology analytics"""
    # Monthly test volume (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_volume = PathologyOrder.objects.filter(
        order_date__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    monthly_test_volume = {
        item['month'].strftime('%Y-%m'): item['count'] 
        for item in monthly_volume
    }
    
    # Test category distribution
    category_distribution = {}
    for category_code, category_name in PathologyTest.TEST_CATEGORIES:
        count = PathologyOrderTest.objects.filter(
            test__category=category_code
        ).count()
        category_distribution[category_name] = count
    
    # Quality metrics
    total_reports = PathologyReport.objects.count()
    finalized_reports = PathologyReport.objects.filter(status='finalized').count()
    quality_metrics = {
        'report_completion_rate': (finalized_reports / total_reports * 100) if total_reports > 0 else 0,
        'critical_results_rate': (PathologyReport.objects.filter(result_status='critical').count() / total_reports * 100) if total_reports > 0 else 0,
        'average_confidence_level': PathologyReport.objects.aggregate(Avg('confidence_level'))['confidence_level__avg'] or 0
    }
    
    analytics_data = {
        'monthly_test_volume': monthly_test_volume,
        'test_category_distribution': category_distribution,
        'turnaround_time_trends': {},  # Could be implemented based on specific needs
        'quality_metrics': quality_metrics,
        'department_performance': {},  # Could be implemented based on specific needs
        'pathologist_workload': {}  # Could be implemented based on specific needs
    }
    
    serializer = PathologyAnalyticsSerializer(analytics_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_statistics(request):
    """Get statistics for each test type"""
    test_stats = []
    
    for test in PathologyTest.objects.filter(is_active=True):
        order_tests = PathologyOrderTest.objects.filter(test=test)
        reports = PathologyReport.objects.filter(order_test__test=test)
        
        normal_count = reports.filter(result_status='normal').count()
        abnormal_count = reports.filter(result_status='abnormal').count()
        critical_count = reports.filter(result_status='critical').count()
        
        # Calculate average turnaround time for this test
        completed_tests = order_tests.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        turnaround_times = []
        for ot in completed_tests:
            if ot.started_at and ot.completed_at:
                delta = ot.completed_at - ot.started_at
                turnaround_times.append(delta.total_seconds() / 3600)
        
        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
        
        test_stats.append({
            'test_name': test.name,
            'test_count': order_tests.count(),
            'normal_results': normal_count,
            'abnormal_results': abnormal_count,
            'critical_results': critical_count,
            'avg_turnaround_time': round(avg_turnaround, 2)
        })
    
    serializer = TestStatisticsSerializer(test_stats, many=True)
    return Response(serializer.data)


# S3 Data Management Views

from .models import PathologyLaboratory, PathologyPatient, PathologySpecimen, PathologyFile, PathologyAnalysis
from .serializers import (
    PathologyLaboratorySerializer, PathologyPatientSerializer, PathologySpecimenSerializer,
    PathologyFileSerializer, PathologyAnalysisSerializer
)
from .services.s3_data_manager import pathology_s3_manager
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class PathologyLaboratoryViewSet(viewsets.ModelViewSet):
    """Pathology Laboratory management for S3 data"""
    queryset = PathologyLaboratory.objects.all()
    serializer_class = PathologyLaboratorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyLaboratory.objects.all()
        laboratory_type = self.request.query_params.get('laboratory_type', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if laboratory_type:
            queryset = queryset.filter(laboratory_type=laboratory_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for specific laboratory"""
        laboratory = self.get_object()
        
        analytics_data = {
            'total_patients': laboratory.patients.count(),
            'total_specimens': laboratory.specimens.count(),
            'total_files': laboratory.files.count(),
            'active_patients': laboratory.patients.filter(is_active=True).count(),
            'recent_files': laboratory.files.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'file_types': {},
            'specimen_types': {}
        }
        
        # File type distribution
        for file_obj in laboratory.files.all():
            file_type = file_obj.file_type
            analytics_data['file_types'][file_type] = analytics_data['file_types'].get(file_type, 0) + 1
        
        # Specimen type distribution
        for specimen in laboratory.specimens.all():
            specimen_type = specimen.specimen_type
            analytics_data['specimen_types'][specimen_type] = analytics_data['specimen_types'].get(specimen_type, 0) + 1
        
        return Response(analytics_data)


class PathologyPatientViewSet(viewsets.ModelViewSet):
    """Pathology Patient management for S3 data"""
    queryset = PathologyPatient.objects.all()
    serializer_class = PathologyPatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyPatient.objects.all()
        laboratory_id = self.request.query_params.get('laboratory_id', None)
        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)
        
        if laboratory_id:
            queryset = queryset.filter(laboratory_id=laboratory_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(patient_id__icontains=search)
            )
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get all files for a patient"""
        patient = self.get_object()
        files = patient.files.all().order_by('-created_at')
        serializer = PathologyFileSerializer(files, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def specimens(self, request, pk=None):
        """Get all specimens for a patient"""
        patient = self.get_object()
        specimens = patient.specimens.all().order_by('-created_at')
        serializer = PathologySpecimenSerializer(specimens, many=True)
        return Response(serializer.data)


class PathologySpecimenViewSet(viewsets.ModelViewSet):
    """Pathology Specimen management"""
    queryset = PathologySpecimen.objects.all()
    serializer_class = PathologySpecimenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologySpecimen.objects.all()
        patient_id = self.request.query_params.get('patient_id', None)
        laboratory_id = self.request.query_params.get('laboratory_id', None)
        specimen_type = self.request.query_params.get('specimen_type', None)
        status = self.request.query_params.get('status', None)
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if laboratory_id:
            queryset = queryset.filter(laboratory_id=laboratory_id)
        if specimen_type:
            queryset = queryset.filter(specimen_type=specimen_type)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get all files for a specimen"""
        specimen = self.get_object()
        files = specimen.files.all().order_by('-created_at')
        serializer = PathologyFileSerializer(files, many=True)
        return Response(serializer.data)


class PathologyFileViewSet(viewsets.ModelViewSet):
    """Pathology File management for S3"""
    queryset = PathologyFile.objects.all()
    serializer_class = PathologyFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = PathologyFile.objects.all()
        laboratory_id = self.request.query_params.get('laboratory_id', None)
        patient_id = self.request.query_params.get('patient_id', None)
        specimen_id = self.request.query_params.get('specimen_id', None)
        file_type = self.request.query_params.get('file_type', None)
        
        if laboratory_id:
            queryset = queryset.filter(laboratory_id=laboratory_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if specimen_id:
            queryset = queryset.filter(specimen_id=specimen_id)
        if file_type:
            queryset = queryset.filter(file_type=file_type)
            
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Upload file to S3 and create database record"""
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            laboratory_id = request.data.get('laboratory_id')
            patient_id = request.data.get('patient_id')
            specimen_id = request.data.get('specimen_id')
            file_type = request.data.get('file_type', 'general')
            description = request.data.get('description', '')
            
            # Upload to S3
            upload_result = pathology_s3_manager.upload_pathology_file(
                file_obj=file_obj,
                laboratory_id=laboratory_id,
                patient_id=patient_id,
                specimen_id=specimen_id,
                file_type=file_type,
                metadata={'description': description}
            )
            
            if upload_result['success']:
                file_record = PathologyFile.objects.get(id=upload_result['file_id'])
                file_record.uploaded_by = request.user
                file_record.description = description
                file_record.save()
                
                serializer = self.get_serializer(file_record)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': upload_result['error']}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def download_url(self, request, pk=None):
        """Generate presigned URL for file download"""
        file_obj = self.get_object()
        presigned_url = pathology_s3_manager.generate_presigned_url(file_obj.s3_key)
        
        if presigned_url:
            return Response({'download_url': presigned_url})
        else:
            return Response({'error': 'Could not generate download URL'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger AI analysis on the file"""
        file_obj = self.get_object()
        analysis_type = request.data.get('analysis_type', 'cell_morphology')
        
        result = pathology_s3_manager.analyze_microscopy_image(file_obj.id, analysis_type)
        
        if result.get('success'):
            return Response(result)
        else:
            return Response({'error': result.get('error')}, status=status.HTTP_400_BAD_REQUEST)


class PathologyAnalysisViewSet(viewsets.ModelViewSet):
    """Pathology Analysis management"""
    queryset = PathologyAnalysis.objects.all()
    serializer_class = PathologyAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PathologyAnalysis.objects.all()
        file_id = self.request.query_params.get('file_id', None)
        analysis_type = self.request.query_params.get('analysis_type', None)
        status_filter = self.request.query_params.get('status', None)
        
        if file_id:
            queryset = queryset.filter(file_id=file_id)
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate analysis results"""
        analysis = self.get_object()
        analysis.is_validated = True
        analysis.reviewed_by = request.user
        analysis.review_notes = request.data.get('review_notes', '')
        analysis.save()
        
        serializer = self.get_serializer(analysis)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pathology_s3_analytics(request):
    """Get comprehensive S3 storage analytics for pathology"""
    try:
        analytics = pathology_s3_manager.get_storage_analytics()
        return Response(analytics)
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pathology_s3_sync(request):
    """Synchronize S3 files with database"""
    try:
        sync_result = pathology_s3_manager.sync_files_with_database()
        return Response(sync_result)
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pathology_cleanup_files(request):
    """Cleanup old pathology files"""
    try:
        days_old = int(request.data.get('days_old', 180))
        cleanup_result = pathology_s3_manager.cleanup_old_files(days_old)
        return Response(cleanup_result)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pathology_report(request):
    """Generate comprehensive pathology report"""
    try:
        patient_id = request.data.get('patient_id')
        analysis_ids = request.data.get('analysis_ids', [])
        
        if not patient_id:
            return Response({'error': 'Patient ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        report_result = pathology_s3_manager.generate_pathology_report(patient_id, analysis_ids)
        return Response(report_result)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
