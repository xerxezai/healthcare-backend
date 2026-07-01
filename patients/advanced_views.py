from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
import json
import uuid
from datetime import datetime, timedelta

from .models import Patient, Appointment, VitalSigns, LabResult
from .advanced_models import (
    PatientAdmission, PatientJourney, AIPatientInsights, 
    PatientReport, PatientMetrics
)
from .serializers import (
    PatientAdmissionSerializer, PatientJourneySerializer,
    AIPatientInsightsSerializer, PatientReportSerializer,
    PatientMetricsSerializer
)
from .ai_services import AIPatientAnalyzer
from .report_generator import PatientReportGenerator

class PatientAdmissionViewSet(viewsets.ModelViewSet):
    """
    Complete Patient Admission Management API
    Handles admission from entry to discharge with comprehensive tracking
    """
    queryset = PatientAdmission.objects.all()
    serializer_class = PatientAdmissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['current_status', 'priority_level', 'department', 'admission_type']
    search_fields = ['admission_id', 'patient__first_name', 'patient__last_name', 'patient__phone']
    ordering_fields = ['admission_date', 'priority_level', 'ai_risk_score']
    ordering = ['-admission_date']

    def get_queryset(self):
        """Filter based on user permissions and active admissions"""
        queryset = self.queryset
        
        # Filter by active admissions if requested
        if self.request.query_params.get('active_only'):
            queryset = queryset.filter(is_active=True, current_status__in=[
                'admitted', 'in_treatment', 'stable', 'critical', 'recovery'
            ])
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(admission_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(admission_date__lte=end_date)
            
        return queryset.select_related('patient', 'attending_physician', 'created_by')

    def perform_create(self, serializer):
        """Create new patient admission with auto-generated ID"""
        # Generate unique admission ID
        admission_id = f"ADM-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Save admission
        admission = serializer.save(
            admission_id=admission_id,
            created_by=self.request.user
        )
        
        # Create initial journey event
        PatientJourney.objects.create(
            admission=admission,
            patient=admission.patient,
            stage='admission',
            location=admission.department,
            action_taken=f"Patient admitted with {admission.chief_complaint}",
            staff_member=self.request.user
        )
        
        # Initialize AI analysis
        ai_analyzer = AIPatientAnalyzer()
        ai_analyzer.analyze_admission_risk(admission)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update patient status with journey tracking"""
        admission = self.get_object()
        new_status = request.data.get('status')
        location = request.data.get('location', 'Unknown')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(PatientAdmission.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        old_status = admission.current_status
        admission.current_status = new_status
        admission.save()
        
        # Create journey event
        PatientJourney.objects.create(
            admission=admission,
            patient=admission.patient,
            stage=self._map_status_to_stage(new_status),
            location=location,
            action_taken=f"Status changed from {old_status} to {new_status}. {notes}",
            staff_member=request.user,
            notes=notes
        )
        
        # Update AI insights if critical status
        if new_status in ['critical', 'discharge_ready']:
            ai_analyzer = AIPatientAnalyzer()
            ai_analyzer.update_patient_insights(admission)
        
        return Response({'message': 'Status updated successfully'})

    @action(detail=True, methods=['post'])
    def discharge_patient(self, request, pk=None):
        """Complete patient discharge process"""
        admission = self.get_object()
        
        with transaction.atomic():
            # Update discharge information
            admission.current_status = 'discharged'
            admission.discharge_date = timezone.now()
            admission.discharge_diagnosis = request.data.get('diagnosis', '')
            admission.discharge_instructions = request.data.get('instructions', '')
            admission.discharge_medications = request.data.get('medications', '')
            admission.follow_up_required = request.data.get('follow_up_required', False)
            admission.follow_up_date = request.data.get('follow_up_date')
            admission.is_active = False
            admission.save()
            
            # Create discharge journey event
            PatientJourney.objects.create(
                admission=admission,
                patient=admission.patient,
                stage='discharge',
                location='Discharge Desk',
                action_taken=f"Patient discharged. Diagnosis: {admission.discharge_diagnosis}",
                staff_member=request.user,
                notes=admission.discharge_instructions
            )
            
            # Calculate final metrics
            self._calculate_final_metrics(admission)
            
            # Generate discharge report
            report_generator = PatientReportGenerator()
            discharge_report = report_generator.generate_discharge_summary(admission)
        
        return Response({
            'message': 'Patient discharged successfully',
            'discharge_report_id': discharge_report.report_id
        })

    @action(detail=True, methods=['get'])
    def patient_journey(self, request, pk=None):
        """Get complete patient journey timeline"""
        admission = self.get_object()
        journey_events = admission.journey_events.all().order_by('timestamp')
        
        timeline_data = []
        for event in journey_events:
            timeline_data.append({
                'id': event.id,
                'stage': event.stage,
                'timestamp': event.timestamp,
                'location': event.location,
                'action': event.action_taken,
                'staff_member': event.staff_member.full_name if event.staff_member else 'System',
                'notes': event.notes,
                'vital_signs': event.vital_signs,
                'duration_minutes': event.duration_minutes,
                'wait_time_minutes': event.wait_time_minutes
            })
        
        return Response({
            'admission_id': admission.admission_id,
            'patient_name': admission.patient.full_name,
            'timeline': timeline_data,
            'total_events': len(timeline_data),
            'length_of_stay': admission.length_of_stay
        })

    @action(detail=True, methods=['get'])
    def ai_insights(self, request, pk=None):
        """Get AI-generated insights for patient"""
        admission = self.get_object()
        insights = admission.ai_insights.all().order_by('-generated_at')
        
        insights_data = []
        for insight in insights:
            insights_data.append({
                'type': insight.insight_type,
                'confidence': insight.confidence_level,
                'risk_score': insight.risk_score,
                'predictions': insight.prediction_data,
                'recommendations': insight.recommendations,
                'risk_factors': insight.risk_factors,
                'generated_at': insight.generated_at,
                'is_validated': insight.is_validated
            })
        
        return Response({
            'admission_id': admission.admission_id,
            'patient_name': admission.patient.full_name,
            'insights': insights_data,
            'overall_risk_score': admission.ai_risk_score
        })

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for patient management"""
        today = timezone.now().date()
        
        # Active admissions
        active_admissions = PatientAdmission.objects.filter(is_active=True)
        
        # Today's statistics
        todays_admissions = PatientAdmission.objects.filter(admission_date__date=today)
        todays_discharges = PatientAdmission.objects.filter(discharge_date__date=today)
        
        # Status distribution
        status_distribution = active_admissions.values('current_status').annotate(
            count=Count('id')
        )
        
        # Priority distribution
        priority_distribution = active_admissions.values('priority_level').annotate(
            count=Count('id')
        )
        
        # Department-wise patient count
        department_stats = active_admissions.values('department').annotate(
            count=Count('id'),
            avg_length_of_stay=Avg('admission_date')
        )
        
        # AI Risk Analysis
        high_risk_patients = active_admissions.filter(ai_risk_score__gte=7.0).count()
        medium_risk_patients = active_admissions.filter(
            ai_risk_score__gte=4.0, ai_risk_score__lt=7.0
        ).count()
        low_risk_patients = active_admissions.filter(ai_risk_score__lt=4.0).count()
        
        return Response({
            'active_admissions': active_admissions.count(),
            'todays_admissions': todays_admissions.count(),
            'todays_discharges': todays_discharges.count(),
            'status_distribution': list(status_distribution),
            'priority_distribution': list(priority_distribution),
            'department_stats': list(department_stats),
            'risk_analysis': {
                'high_risk': high_risk_patients,
                'medium_risk': medium_risk_patients,
                'low_risk': low_risk_patients
            },
            'total_capacity': 200,  # This should come from hospital settings
            'occupancy_rate': min((active_admissions.count() / 200) * 100, 100)
        })

    def _map_status_to_stage(self, status):
        """Map admission status to journey stage"""
        status_stage_map = {
            'admitted': 'admission',
            'in_treatment': 'treatment',
            'stable': 'monitoring',
            'critical': 'monitoring',
            'recovery': 'recovery',
            'discharge_ready': 'discharge_planning',
            'discharged': 'discharge'
        }
        return status_stage_map.get(status, 'monitoring')

    def _calculate_final_metrics(self, admission):
        """Calculate and store final patient metrics"""
        try:
            metrics, created = PatientMetrics.objects.get_or_create(admission=admission)
            
            # Calculate time metrics from journey events
            journey_events = admission.journey_events.all().order_by('timestamp')
            
            if journey_events.exists():
                first_event = journey_events.first()
                last_event = journey_events.last()
                
                # Calculate total stay duration
                if admission.discharge_date:
                    total_minutes = (admission.discharge_date - admission.admission_date).total_seconds() / 60
                    metrics.door_to_doctor_minutes = int(total_minutes)
            
            # Calculate other metrics
            vital_signs_count = VitalSigns.objects.filter(patient=admission.patient).count()
            metrics.vital_signs_frequency = vital_signs_count
            
            # Calculate satisfaction score (placeholder - would come from patient feedback)
            metrics.satisfaction_score = 8.5  # Default good score
            
            # Calculate costs (placeholder - would come from billing system)
            metrics.total_cost = admission.estimated_cost or 0
            
            metrics.save()
            
        except Exception as e:
            # Log error but don't fail the discharge process
            print(f"Error calculating metrics for {admission.admission_id}: {str(e)}")

class PatientJourneyViewSet(viewsets.ModelViewSet):
    """
    Patient Journey Event Management
    Track individual events in patient care timeline
    """
    queryset = PatientJourney.objects.all()
    serializer_class = PatientJourneySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stage', 'admission__admission_id']
    ordering = ['timestamp']

    @action(detail=False, methods=['post'])
    def add_event(self, request):
        """Add new journey event for patient"""
        admission_id = request.data.get('admission_id')
        admission = get_object_or_404(PatientAdmission, admission_id=admission_id)
        
        journey_event = PatientJourney.objects.create(
            admission=admission,
            patient=admission.patient,
            stage=request.data.get('stage'),
            location=request.data.get('location'),
            action_taken=request.data.get('action_taken'),
            staff_member=request.user,
            notes=request.data.get('notes', ''),
            vital_signs=request.data.get('vital_signs', {}),
            duration_minutes=request.data.get('duration_minutes'),
            wait_time_minutes=request.data.get('wait_time_minutes')
        )
        
        serializer = self.get_serializer(journey_event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PatientReportViewSet(viewsets.ModelViewSet):
    """
    Patient Report Generation and Management
    Handle comprehensive patient reporting with AI analysis
    """
    queryset = PatientReport.objects.all()
    serializer_class = PatientReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['report_type', 'status', 'admission__admission_id']
    search_fields = ['report_id', 'title']

    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate comprehensive patient report"""
        admission_id = request.data.get('admission_id')
        report_type = request.data.get('report_type', 'comprehensive')
        
        admission = get_object_or_404(PatientAdmission, admission_id=admission_id)
        
        # Generate unique report ID
        report_id = f"RPT-{timezone.now().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Create report record
        report = PatientReport.objects.create(
            admission=admission,
            patient=admission.patient,
            report_id=report_id,
            report_type=report_type,
            title=f"{report_type.replace('_', ' ').title()} Report - {admission.patient.full_name}",
            generated_by=request.user,
            status='generating'
        )
        
        try:
            # Generate report content
            report_generator = PatientReportGenerator()
            
            if report_type == 'comprehensive':
                content = report_generator.generate_comprehensive_report(admission)
            elif report_type == 'discharge_summary':
                content = report_generator.generate_discharge_summary(admission)
            elif report_type == 'ai_analysis':
                content = report_generator.generate_ai_analysis_report(admission)
            else:
                content = report_generator.generate_basic_report(admission)
            
            # Update report with content
            report.content = content
            report.summary = content.get('summary', '')
            report.status = 'completed'
            report.save()
            
            # Log access
            report.log_access(request.user, 'generated')
            
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            report.status = 'error'
            report.save()
            return Response(
                {'error': f'Report generation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        report = self.get_object()
        
        # Log access
        report.log_access(request.user, 'downloaded')
        
        # Return file content or redirect to file URL
        return Response({
            'report_id': report.report_id,
            'download_url': f'/api/reports/{report.report_id}/file/',
            'file_format': report.file_format,
            'generated_at': report.generated_at
        })

class AIPatientInsightsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AI Patient Insights Management
    Provide AI-generated predictions and recommendations
    """
    queryset = AIPatientInsights.objects.all()
    serializer_class = AIPatientInsightsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['insight_type', 'confidence_level', 'admission__admission_id']

    @action(detail=False, methods=['post'])
    def generate_insights(self, request):
        """Generate AI insights for patient admission"""
        admission_id = request.data.get('admission_id')
        insight_types = request.data.get('insight_types', ['risk_assessment'])
        
        admission = get_object_or_404(PatientAdmission, admission_id=admission_id)
        
        ai_analyzer = AIPatientAnalyzer()
        insights = []
        
        for insight_type in insight_types:
            insight = ai_analyzer.generate_insight(admission, insight_type)
            if insight:
                insights.append(insight)
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def validate_insight(self, request, pk=None):
        """Validate AI insight by medical professional"""
        insight = self.get_object()
        
        insight.is_validated = request.data.get('is_validated', False)
        insight.validation_notes = request.data.get('validation_notes', '')
        insight.validated_by = request.user
        insight.save()
        
        return Response({'message': 'Insight validation updated'})

class PatientAnalyticsViewSet(viewsets.ViewSet):
    """
    Advanced Patient Analytics and KPIs
    Provide comprehensive analytics for hospital management
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def quality_metrics(self, request):
        """Get patient care quality metrics"""
        # Time period filter
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        admissions = PatientAdmission.objects.filter(admission_date__gte=start_date)
        metrics = PatientMetrics.objects.filter(admission__in=admissions)
        
        # Calculate averages
        avg_length_of_stay = admissions.aggregate(
            avg_los=Avg('admission_date')
        )['avg_los'] or 0
        
        avg_satisfaction = metrics.aggregate(
            avg_satisfaction=Avg('satisfaction_score')
        )['avg_satisfaction'] or 0
        
        # Calculate readmission rate
        total_discharged = admissions.filter(current_status='discharged').count()
        readmissions = metrics.filter(readmission_30_days=True).count()
        readmission_rate = (readmissions / total_discharged * 100) if total_discharged > 0 else 0
        
        # Quality indicators
        quality_indicators = {
            'medication_errors': metrics.aggregate(Sum('medication_errors'))['medication_errors__sum'] or 0,
            'falls_incidents': metrics.aggregate(Sum('falls_incidents'))['falls_incidents__sum'] or 0,
            'hospital_infections': metrics.filter(hospital_acquired_infections=True).count(),
            'pressure_ulcers': metrics.filter(pressure_ulcers=True).count()
        }
        
        return Response({
            'period_days': days,
            'total_admissions': admissions.count(),
            'avg_length_of_stay': round(avg_length_of_stay, 1),
            'avg_satisfaction_score': round(avg_satisfaction, 1),
            'readmission_rate': round(readmission_rate, 2),
            'quality_indicators': quality_indicators,
            'benchmark_comparison': {
                'length_of_stay_benchmark': 4.5,
                'satisfaction_benchmark': 8.0,
                'readmission_benchmark': 10.0
            }
        })

    @action(detail=False, methods=['get'])
    def predictive_analytics(self, request):
        """Get predictive analytics for resource planning"""
        # This would integrate with ML models for predictions
        # For now, providing mock data structure
        
        return Response({
            'bed_occupancy_forecast': [
                {'date': '2024-01-15', 'predicted_occupancy': 85, 'confidence': 0.92},
                {'date': '2024-01-16', 'predicted_occupancy': 78, 'confidence': 0.89},
                {'date': '2024-01-17', 'predicted_occupancy': 82, 'confidence': 0.87}
            ],
            'admission_forecast': [
                {'date': '2024-01-15', 'predicted_admissions': 12, 'confidence': 0.88},
                {'date': '2024-01-16', 'predicted_admissions': 15, 'confidence': 0.85},
                {'date': '2024-01-17', 'predicted_admissions': 18, 'confidence': 0.83}
            ],
            'resource_requirements': {
                'nursing_staff': 45,
                'icu_beds': 8,
                'general_beds': 120,
                'emergency_capacity': 95
            },
            'risk_alerts': [
                {
                    'type': 'capacity_warning',
                    'message': 'ICU capacity expected to reach 95% by weekend',
                    'severity': 'medium',
                    'action_required': 'Consider discharge planning for stable patients'
                }
            ]
        })
